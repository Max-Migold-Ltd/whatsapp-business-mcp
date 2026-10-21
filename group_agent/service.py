"""
Wires the group agent's store, WhatsApp bridge client and LLM together.
"""

import logging

from .agent import BridgeClient, GroupAgent
from .config import MODE_REPLY, GroupAgentSettings
from .store import GroupStore

logger = logging.getLogger("group-agent")


class GroupAgentService:
    def __init__(self, settings: GroupAgentSettings):
        if not settings.bridge_secret:
            raise ValueError("BRIDGE_SECRET is required for the group agent")
        self.settings = settings
        self.store = GroupStore(settings.database_url or settings.db_path)
        self.bridge = BridgeClient(settings.bridge_url, settings.bridge_secret)
        self.agent = GroupAgent(settings, self.store, self.bridge)

    async def start(self) -> None:
        s = self.settings
        logger.info("Group agent started - mode: %s, LLM: %s", s.mode, self.agent.llm.name)
        if s.mode == MODE_REPLY:
            logger.info("May reply in: %s", ", ".join(s.reply_chats) or "nowhere (GROUP_AGENT_REPLY_CHATS is empty)")

    async def stop(self) -> None:
        self.agent.stop()
        self.store.close()
