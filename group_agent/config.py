"""
Settings for the WhatsApp group agent, read from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional, Tuple

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

MODE_LISTEN = "listen"  # read and store everything, never reply
MODE_REPLY = "reply"    # may reply, but only in GROUP_AGENT_REPLY_CHATS


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class GroupAgentSettings:
    enabled: bool
    mode: str
    reply_chats: Tuple[str, ...]  # group ids or names; "*" = every chat
    assistant_name: str
    prompt_file: str

    # WhatsApp bridge (wa_bridge/)
    bridge_url: str
    bridge_secret: Optional[str]

    # Any OpenAI-compatible chat completions API; empty = built-in test mode
    llm_base_url: Optional[str]
    llm_api_key: Optional[str]
    llm_model: Optional[str]
    llm_temperature: float
    llm_timeout: float

    # Pacing
    history_size: int
    debounce_seconds: float
    min_reply_gap_seconds: float

    # Storage (shared with the support bot)
    database_url: Optional[str]
    db_path: str

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_model)

    @classmethod
    def from_env(cls) -> "GroupAgentSettings":
        mode = os.getenv("GROUP_AGENT_MODE", MODE_LISTEN).strip().lower()
        if mode not in (MODE_LISTEN, MODE_REPLY):
            raise ValueError(f"GROUP_AGENT_MODE must be '{MODE_LISTEN}' or '{MODE_REPLY}', not '{mode}'")
        chats = tuple(c.strip() for c in os.getenv("GROUP_AGENT_REPLY_CHATS", "").split(",") if c.strip())
        return cls(
            enabled=_flag("GROUP_AGENT_ENABLED"),
            mode=mode,
            reply_chats=chats,
            assistant_name=os.getenv("ASSISTANT_NAME", "Max Migold Assistant"),
            prompt_file=os.getenv("GROUP_AGENT_PROMPT_FILE", os.path.join(_PACKAGE_DIR, "prompt.md")),
            bridge_url=os.getenv("BRIDGE_URL", "http://127.0.0.1:3100").rstrip("/"),
            bridge_secret=os.getenv("BRIDGE_SECRET") or None,
            llm_base_url=(os.getenv("LLM_BASE_URL") or "").rstrip("/") or None,
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_model=os.getenv("LLM_MODEL") or None,
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            llm_timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
            history_size=int(os.getenv("GROUP_AGENT_HISTORY", "30")),
            debounce_seconds=float(os.getenv("GROUP_AGENT_DEBOUNCE_SECONDS", "6")),
            min_reply_gap_seconds=float(os.getenv("GROUP_AGENT_MIN_REPLY_GAP_SECONDS", "60")),
            database_url=os.getenv("DATABASE_URL") or None,
            db_path=os.getenv("SUPPORT_DB_PATH", os.path.join("data", "support.db")),
        )
