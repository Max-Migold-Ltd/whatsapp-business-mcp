"""
Client for any OpenAI-compatible chat completions API (OpenAI, DeepSeek, Groq,
Together, vLLM, Ollama, LM Studio, ...), with tool (function) calling.

Configured with LLM_BASE_URL (e.g. https://api.deepseek.com/v1), LLM_API_KEY and
LLM_MODEL. Without them, StubLLM is used so the WhatsApp side can be tested first.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("group-agent.llm")


class LLMError(RuntimeError):
    pass


class ChatLLM:
    def __init__(self, base_url: str, api_key: Optional[str], model: str, temperature: float = 0.3, timeout: float = 60):
        self.url = f"{base_url}/chat/completions"
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    @property
    def name(self) -> str:
        return self.model

    async def complete(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Returns the assistant message: {"content": str|None, "tool_calls": [...]}."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body: Dict[str, Any] = {"model": self.model, "messages": messages, "temperature": self.temperature}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.url, headers=headers, json=body)
        if response.status_code != 200:
            raise LLMError(f"LLM request failed ({response.status_code}): {response.text[:300]}")
        try:
            return response.json()["choices"][0]["message"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(f"Unexpected LLM response: {response.text[:300]}") from e


class StubLLM:
    """Test mode until a real LLM is configured: replies only when the assistant is addressed by name."""

    name = "test-mode (no LLM configured)"

    def __init__(self, assistant_name: str):
        self.trigger = assistant_name.split()[-1].lower()  # "assistant"

    async def complete(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        if any(m.get("role") == "tool" for m in messages):
            return {"content": None, "tool_calls": []}  # already replied this round
        new_part = messages[-1]["content"].split("NEW MESSAGES", 1)[-1]
        newest = [line for line in new_part.splitlines() if line.startswith("[msg ") and " You (" not in line]
        addressed = [line for line in newest if self.trigger in line.lower()]
        if not addressed:
            return {"content": None, "tool_calls": []}
        msg_id = addressed[-1].split("]", 1)[0].removeprefix("[msg ").strip()
        return {"content": None, "tool_calls": [{
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {"name": "send_reply", "arguments": json.dumps({
                "text": "Hello! I'm the Max Migold Assistant and I can see this group. "
                        "(Test mode: my full replies will be switched on soon.)",
                "reply_to": msg_id,
            })},
        }]}


def build_llm(settings) -> Any:
    if settings.llm_configured:
        return ChatLLM(
            settings.llm_base_url, settings.llm_api_key, settings.llm_model,
            settings.llm_temperature, settings.llm_timeout,
        )
    return StubLLM(settings.assistant_name)
