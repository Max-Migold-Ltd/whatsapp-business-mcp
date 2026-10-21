"""
The group agent: stores every WhatsApp message, and in reply mode lets the LLM
decide whether to answer, using tools (for now: send_reply).

Messages in a chat are batched for a few seconds (debounce) so a burst of
messages produces one decision, and replies are spaced out per chat.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import httpx

from .config import MODE_REPLY, GroupAgentSettings
from .llm import LLMError, build_llm
from .store import GroupStore

logger = logging.getLogger("group-agent")

MAX_TOOL_ROUNDS = 3

TOOLS: List[Dict[str, Any]] = [{
    "type": "function",
    "function": {
        "name": "send_reply",
        "description": "Send a WhatsApp message in this chat. Only call this when a reply is really needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The message to send (1-3 short sentences)."},
                "reply_to": {"type": "string", "description": "Id of the NEW message you are replying to."},
            },
            "required": ["text"],
        },
    },
}]


class BridgeClient:
    """Talks to wa_bridge (the Node process that holds the WhatsApp connection)."""

    def __init__(self, url: str, secret: Optional[str]):
        self.url = url
        self.headers = {"X-Bridge-Secret": secret or ""}

    async def _get(self, path: str) -> httpx.Response:
        async with httpx.AsyncClient(timeout=15) as client:
            return await client.get(f"{self.url}{path}", headers=self.headers)

    async def health(self) -> Dict[str, Any]:
        return (await self._get("/health")).json()

    async def groups(self) -> List[Dict[str, Any]]:
        return (await self._get("/groups")).json()

    async def qr_png(self) -> Optional[bytes]:
        response = await self._get("/qr")
        return response.content if response.status_code == 200 else None

    async def pairing_code(self, phone: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.url}/pair", headers=self.headers, json={"phone": phone})
        return {"status_code": response.status_code, **response.json()}

    async def send(self, chat: str, text: str, quoted: Optional[str] = None) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.url}/send", headers=self.headers, json={"chat": chat, "text": text, "quoted": quoted}
            )
        if response.status_code != 200:
            raise RuntimeError(f"Bridge could not send ({response.status_code}): {response.text[:200]}")
        return response.json().get("id")


class GroupAgent:
    def __init__(self, settings: GroupAgentSettings, store: GroupStore, bridge: BridgeClient, llm=None):
        self.settings = settings
        self.store = store
        self.bridge = bridge
        self.llm = llm or build_llm(settings)
        with open(settings.prompt_file, encoding="utf-8") as f:
            self.system_prompt = f.read().replace("{assistant_name}", settings.assistant_name)
        self.tz = ZoneInfo("Africa/Lagos")
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._timers: Dict[str, asyncio.Task] = {}
        # Messages stored before this start are context only - never answered after a restart
        row = store.db.one("SELECT MAX(id) AS id FROM group_messages")
        self._start_id = (row["id"] if row else None) or 0
        self._seen: Dict[str, int] = {}

    # ================================
    # INCOMING
    # ================================

    async def handle_event(self, event: Dict[str, Any]) -> None:
        if not event.get("chat") or not event.get("id"):
            return
        if not self.store.add_message(event):
            return  # duplicate, e.g. the echo of our own reply
        if event.get("from_me") or self.settings.mode != MODE_REPLY or not self.may_reply_in(event):
            return
        if self.settings.debounce_seconds <= 0:
            await self.process_chat(event["chat"])
        else:
            self._schedule(event["chat"], self.settings.debounce_seconds)

    def may_reply_in(self, event: Dict[str, Any]) -> bool:
        allowed = self.settings.reply_chats
        if "*" in allowed:
            return True
        name = (event.get("chat_name") or "").strip().lower()
        return any(c == event["chat"] or (name and c.lower() == name) for c in allowed)

    def _schedule(self, chat: str, delay: float) -> None:
        """Debounce: (re)start the timer so a burst of messages is decided on once."""
        if delay <= 0:
            asyncio.ensure_future(self.process_chat(chat))
            return
        timer = self._timers.get(chat)
        if timer and not timer.done():
            timer.cancel()
        self._timers[chat] = asyncio.ensure_future(self._after(chat, delay))

    async def _after(self, chat: str, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        await self.process_chat(chat)

    def stop(self) -> None:
        for timer in self._timers.values():
            timer.cancel()

    # ================================
    # DECIDING
    # ================================

    async def process_chat(self, chat: str) -> None:
        async with self._locks[chat]:
            try:
                await self._decide(chat)
            except Exception:
                logger.exception("Group agent failed while processing chat %s", chat)

    async def _decide(self, chat: str) -> None:
        history = self.store.recent(chat, self.settings.history_size)
        seen = self._seen.get(chat, self._start_id)
        new = [m for m in history if m["id"] > seen and not m["from_me"]]
        if not new:
            return

        last_reply = self.store.last_reply_at(chat)
        wait = (last_reply or 0) + self.settings.min_reply_gap_seconds - time.time()
        if wait > 0:
            self._schedule(chat, wait)  # too soon after our last reply - look again later
            return

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._transcript(history, seen)},
        ]
        replied = False
        for _ in range(MAX_TOOL_ROUNDS):
            try:
                answer = await self.llm.complete(messages, TOOLS)
            except LLMError as e:
                logger.warning("LLM unavailable, will retry on the next message: %s", e)
                return
            calls = answer.get("tool_calls") or []
            if not calls:
                break
            messages.append({"role": "assistant", "content": answer.get("content"), "tool_calls": calls})
            for call in calls:
                result = await self._run_tool(chat, call, replied, {m["msg_id"] for m in new})
                replied = replied or result.get("sent", False)
                messages.append({"role": "tool", "tool_call_id": call.get("id"), "content": json.dumps(result)})
            if replied:
                break

        self._seen[chat] = max(m["id"] for m in new)
        logger.info("Chat %s: %d new message(s), %s", new[-1]["chat_name"] or chat, len(new),
                    "replied" if replied else "stayed silent")

    async def _run_tool(
        self, chat: str, call: Dict[str, Any], already_replied: bool, new_ids: set
    ) -> Dict[str, Any]:
        function = call.get("function") or {}
        try:
            args = json.loads(function.get("arguments") or "{}")
        except ValueError:
            return {"error": "arguments were not valid JSON"}

        if function.get("name") == "send_reply":
            text = (args.get("text") or "").strip()
            if not text:
                return {"error": "text is empty"}
            if already_replied:
                return {"error": "already replied in this chat just now; do not send another message"}
            # Only quote a message the LLM was shown as new; ignore made-up or stale ids
            reply_to = args.get("reply_to") if args.get("reply_to") in new_ids else None
            msg_id = await self.bridge.send(chat, text, reply_to)
            last = self.store.recent(chat, 1)
            self.store.add_message({
                "id": msg_id, "chat": chat, "chat_name": last[0]["chat_name"] if last else None,
                "is_group": chat.endswith("@g.us"), "sender": "me", "sender_name": self.settings.assistant_name,
                "from_me": True, "type": "text", "text": text, "quoted_id": reply_to,
                "timestamp": int(time.time()),
            })
            return {"sent": True, "message_id": msg_id}

        return {"error": f"unknown tool {function.get('name')}"}

    def _transcript(self, history: List[Dict[str, Any]], seen: int) -> str:
        """The chat as the LLM sees it. Names only - no phone numbers are sent to the LLM."""
        name = next((m["chat_name"] for m in reversed(history) if m["chat_name"]), None) or "this chat"
        earlier = [self._line(m) for m in history if m["id"] <= seen]
        new = [self._line(m) for m in history if m["id"] > seen]
        parts = [f"WhatsApp group: {name}", ""]
        if earlier:
            parts += ["EARLIER MESSAGES (context only, already handled):", *earlier, ""]
        parts += ["NEW MESSAGES since you last looked:", *new, "",
                  "Decide whether any NEW message needs a reply. If not, do not call any tool."]
        return "\n".join(parts)

    def _line(self, m: Dict[str, Any]) -> str:
        when = datetime.fromtimestamp(m["ts"], tz=timezone.utc).astimezone(self.tz).strftime("%d %b %H:%M")
        who = f"You ({self.settings.assistant_name})" if m["from_me"] else (m["sender_name"] or "Someone")
        text = m["text"] or f"[{m['msg_type']}]"
        if m["msg_type"] not in ("text", "conversation", "extendedText") and m["text"]:
            text = f"[{m['msg_type']}] {text}"
        reply = f" (replying to msg {m['quoted_id']})" if m["quoted_id"] else ""
        return f"[msg {m['msg_id']}] {when} {who}{reply}: {text}"
