"""
Local SQLite store for conversations and messages.

This is the source of truth: every message is written here first, then copied
to the SharePoint Excel log by the sync loop. If SharePoint is unreachable,
rows simply stay unsynced and are retried later.
"""

import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

# Conversation states
STATE_BOT = "bot"      # the intake bot is asking the customer questions
STATE_AGENT = "agent"  # a human agent is handling it; the bot stays silent

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    phone            TEXT PRIMARY KEY,
    name             TEXT,
    state            TEXT NOT NULL DEFAULT 'bot',
    handoff_at       INTEGER,
    last_customer_at INTEGER,
    last_agent_at    INTEGER,
    step             TEXT,
    answers          TEXT,
    updated_at       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ref        TEXT UNIQUE,
    phone      TEXT NOT NULL,
    name       TEXT,
    answers    TEXT NOT NULL,
    status     TEXT,
    created_at INTEGER NOT NULL,
    synced     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    wamid     TEXT UNIQUE,
    phone     TEXT NOT NULL,
    name      TEXT,
    direction TEXT NOT NULL,
    sender    TEXT NOT NULL,
    msg_type  TEXT,
    body      TEXT,
    ts        INTEGER NOT NULL,
    state     TEXT,
    synced    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_messages_unsynced ON messages(synced, id);
CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone, ts);
CREATE INDEX IF NOT EXISTS idx_tickets_unsynced ON tickets(synced, id);

-- Relay mode: which resident each message forwarded to the agent belongs to
CREATE TABLE IF NOT EXISTS relay_links (
    wamid      TEXT PRIMARY KEY,
    phone      TEXT NOT NULL,
    ref        TEXT,
    payload    TEXT,
    created_at INTEGER NOT NULL
);

-- Relay mode: agent messages already handled (Meta retries webhooks)
CREATE TABLE IF NOT EXISTS seen_events (
    wamid      TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL
);

-- Relay mode: forwards waiting until the agent's 24-hour window is open again
CREATE TABLE IF NOT EXISTS relay_queue (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    payload    TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
"""

# Conversation fields that may be explicitly cleared by passing None
_CLEARABLE = {"handoff_at", "step", "answers"}


class SupportStore:
    """Thread-safe wrapper around a single SQLite connection."""

    def __init__(self, db_path: str):
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._migrate()
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def _migrate(self) -> None:
        """Add columns introduced after the first release to an existing database."""
        for table, new_columns in (
            ("conversations", ("step", "answers")), ("tickets", ("ref", "status")), ("relay_links", ("payload",)),
        ):
            columns = {row[1] for row in self._conn.execute(f"PRAGMA table_info({table})")}
            if columns:
                for column in new_columns:
                    if column not in columns:
                        self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ================================
    # CONVERSATIONS
    # ================================

    def get_conversation(self, phone: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM conversations WHERE phone = ?", (phone,)).fetchone()
        return dict(row) if row else None

    def upsert_conversation(self, phone: str, **fields: Any) -> Dict[str, Any]:
        """Create the conversation if needed and update the given fields."""
        fields = {k: v for k, v in fields.items() if v is not None or k in _CLEARABLE}
        fields["updated_at"] = int(time.time())
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO conversations (phone, state, updated_at) VALUES (?, ?, ?)",
                (phone, STATE_BOT, fields["updated_at"]),
            )
            assignments = ", ".join(f"{column} = ?" for column in fields)
            self._conn.execute(
                f"UPDATE conversations SET {assignments} WHERE phone = ?",
                (*fields.values(), phone),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM conversations WHERE phone = ?", (phone,)).fetchone()
        return dict(row)

    def list_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ================================
    # MESSAGES
    # ================================

    def add_message(
        self,
        phone: str,
        direction: str,
        sender: str,
        msg_type: str,
        body: str,
        ts: Optional[int] = None,
        wamid: Optional[str] = None,
        name: Optional[str] = None,
        state: Optional[str] = None,
    ) -> bool:
        """Store a message. Returns False if a message with this WhatsApp ID was already stored
        (Meta retries webhooks, so duplicates are expected)."""
        with self._lock:
            cursor = self._conn.execute(
                """INSERT OR IGNORE INTO messages
                   (wamid, phone, name, direction, sender, msg_type, body, ts, state)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (wamid, phone, name, direction, sender, msg_type, body, ts or int(time.time()), state),
            )
            self._conn.commit()
        return cursor.rowcount == 1

    def has_message(self, wamid: str) -> bool:
        with self._lock:
            row = self._conn.execute("SELECT 1 FROM messages WHERE wamid = ?", (wamid,)).fetchone()
        return row is not None

    def get_messages(self, phone: Optional[str] = None, limit: int = 10000) -> List[Dict[str, Any]]:
        query = "SELECT * FROM messages"
        params: tuple = ()
        if phone:
            query += " WHERE phone = ?"
            params = (phone,)
        query += " ORDER BY ts, id LIMIT ?"
        with self._lock:
            rows = self._conn.execute(query, (*params, limit)).fetchall()
        return [dict(r) for r in rows]

    def get_unsynced(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM messages WHERE synced = 0 ORDER BY id LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_synced(self, ids: List[int]) -> None:
        if not ids:
            return
        with self._lock:
            self._conn.executemany("UPDATE messages SET synced = 1 WHERE id = ?", [(i,) for i in ids])
            self._conn.commit()

    # ================================
    # TICKETS (one per completed intake)
    # ================================

    def create_ticket(
        self, phone: str, name: Optional[str], answers: Dict[str, str], prefix: str, status: str
    ) -> Dict[str, Any]:
        """Save a ticket and give it a reference like MMF-00042."""
        with self._lock:
            cursor = self._conn.execute(
                "INSERT INTO tickets (phone, name, answers, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (phone, name, json.dumps(answers, ensure_ascii=False), status, int(time.time())),
            )
            ref = format_ticket_ref(prefix, cursor.lastrowid)
            self._conn.execute("UPDATE tickets SET ref = ? WHERE id = ?", (ref, cursor.lastrowid))
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM tickets WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _ticket(row)

    def get_ticket(self, ref: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM tickets WHERE ref = ?", (ref,)).fetchone()
        return _ticket(row) if row else None

    def set_ticket_status(self, ref: str, status: str) -> None:
        with self._lock:
            self._conn.execute("UPDATE tickets SET status = ? WHERE ref = ?", (status, ref))
            self._conn.commit()

    def list_tickets(self, limit: int = 1000, unsynced_only: bool = False) -> List[Dict[str, Any]]:
        query = "SELECT * FROM tickets"
        if unsynced_only:
            query += " WHERE synced = 0 ORDER BY id"
        else:
            query += " ORDER BY id DESC"
        with self._lock:
            rows = self._conn.execute(query + " LIMIT ?", (limit,)).fetchall()
        return [_ticket(row) for row in rows]

    def mark_tickets_synced(self, ids: List[int]) -> None:
        if not ids:
            return
        with self._lock:
            self._conn.executemany("UPDATE tickets SET synced = 1 WHERE id = ?", [(i,) for i in ids])
            self._conn.commit()


    def latest_ticket(self, phone: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM tickets WHERE phone = ? ORDER BY id DESC LIMIT 1", (phone,)
            ).fetchone()
        return _ticket(row) if row else None

    # ================================
    # RELAY MODE
    # ================================

    def add_relay_link(self, wamid: str, phone: str, ref: Optional[str], payload: Dict[str, Any]) -> None:
        """Remember a forward: who it belongs to, and its content in case Meta later reports it undelivered."""
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO relay_links (wamid, phone, ref, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (wamid, phone, ref, json.dumps(payload, ensure_ascii=False), int(time.time())),
            )
            self._conn.commit()

    def get_relay_link(self, wamid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM relay_links WHERE wamid = ?", (wamid,)).fetchone()
        return dict(row) if row else None

    def mark_seen(self, wamid: Optional[str]) -> bool:
        """Record an event ID. Returns False if it was already seen."""
        if not wamid:
            return True
        with self._lock:
            cursor = self._conn.execute(
                "INSERT OR IGNORE INTO seen_events (wamid, created_at) VALUES (?, ?)", (wamid, int(time.time()))
            )
            self._conn.commit()
        return cursor.rowcount == 1

    def enqueue_relay(self, payload: Dict[str, Any]) -> int:
        """Queue a forward for later. Returns how many are now waiting."""
        with self._lock:
            self._conn.execute(
                "INSERT INTO relay_queue (payload, created_at) VALUES (?, ?)",
                (json.dumps(payload, ensure_ascii=False), int(time.time())),
            )
            self._conn.commit()
            return self._conn.execute("SELECT COUNT(*) FROM relay_queue").fetchone()[0]

    def take_relay_queue(self) -> List[Dict[str, Any]]:
        """Remove and return all queued forwards, oldest first."""
        with self._lock:
            rows = self._conn.execute("SELECT id, payload FROM relay_queue ORDER BY id").fetchall()
            self._conn.execute("DELETE FROM relay_queue")
            self._conn.commit()
        return [json.loads(row["payload"]) for row in rows]


def format_ticket_ref(prefix: str, ticket_id: int) -> str:
    return f"{prefix}-{ticket_id:05d}"


def _ticket(row: sqlite3.Row) -> Dict[str, Any]:
    ticket = dict(row)
    ticket["answers"] = json.loads(ticket["answers"])
    return ticket
