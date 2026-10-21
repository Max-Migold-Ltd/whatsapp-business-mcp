"""
Tests for the WhatsApp group agent: bridge events in, LLM decisions, replies out.
The WhatsApp bridge and the LLM are faked - nothing is sent anywhere.
"""

import asyncio
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

SECRET = "test-bridge-secret"
API_KEY = "test-api-key"
GROUP = "120363000000000001@g.us"
OTHER_GROUP = "120363000000000002@g.us"
RESIDENT = "2348012345678@s.whatsapp.net"


@pytest.fixture
def env(monkeypatch, tmp_path):
    values = {
        "META_ACCESS_TOKEN": "EAAtesttoken", "META_PHONE_NUMBER_ID": "1111111111", "WABA_ID": "2222222222",
        "META_APP_SECRET": "x", "WEBHOOK_VERIFY_TOKEN": "x", "MCP_API_KEY": API_KEY,
        "SUPPORT_DB_PATH": str(tmp_path / "support.db"),
        "GROUP_AGENT_ENABLED": "true", "GROUP_AGENT_MODE": "reply", "GROUP_AGENT_REPLY_CHATS": "La Tour Residents",
        "BRIDGE_SECRET": SECRET, "GROUP_AGENT_DEBOUNCE_SECONDS": "0", "GROUP_AGENT_MIN_REPLY_GAP_SECONDS": "60",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    for key in ("DATABASE_URL", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "AGENT_WHATSAPP_NUMBER",
                "SHAREPOINT_TENANT_ID", "SHAREPOINT_FILE_URL"):
        monkeypatch.delenv(key, raising=False)
    return values


@pytest.fixture
def sent(monkeypatch):
    """Messages the agent asks the bridge to send."""
    from group_agent.agent import BridgeClient

    calls = []

    async def fake_send(self, chat, text, quoted=None):
        calls.append({"chat": chat, "text": text, "quoted": quoted})
        return f"OUT{len(calls)}"

    monkeypatch.setattr(BridgeClient, "send", fake_send)
    return calls


@pytest.fixture
def client(env, sent):
    import main_http

    with TestClient(main_http.app) as test_client:
        yield test_client


def event(msg_id, text, chat=GROUP, chat_name="La Tour Residents", from_me=False, sender=RESIDENT, name="Ada Obi"):
    return {
        "id": msg_id, "chat": chat, "chat_name": chat_name, "is_group": True, "sender": sender,
        "sender_name": name, "from_me": from_me, "type": "conversation", "text": text,
        "quoted_id": None, "mentions": [], "timestamp": int(time.time()),
    }


def post(client, payload, secret=SECRET):
    return client.post("/group-agent/events", json=payload, headers={"X-Bridge-Secret": secret})


def agent(client):
    return client.app.state.group_agent.agent


def stored(client, chat=GROUP):
    return client.app.state.group_agent.store.recent(chat, 100)


# ================================
# SEEING MESSAGES
# ================================

def test_rejects_wrong_bridge_secret(client, sent):
    assert post(client, event("M1", "hello"), secret="wrong").status_code == 403
    assert stored(client) == []


def test_every_message_is_stored(client, sent):
    post(client, event("M1", "Good morning everyone"))
    post(client, event("M2", "Light is back in Block A", name="Tunde"))
    rows = stored(client)
    assert [(r["msg_id"], r["sender_name"], r["text"]) for r in rows] == [
        ("M1", "Ada Obi", "Good morning everyone"), ("M2", "Tunde", "Light is back in Block A"),
    ]
    assert rows[0]["chat_name"] == "La Tour Residents"


def test_duplicates_and_own_messages_are_not_answered(client, sent):
    post(client, event("M1", "assistant are you there?"))
    post(client, event("M1", "assistant are you there?"))  # bridge retry
    post(client, event("OUT1", "Hello!", from_me=True))     # echo of our own reply
    assert len(sent) == 1
    assert len(stored(client)) == 2


def test_status_endpoint(client, sent):
    post(client, event("M1", "hi"))
    response = client.get("/api/v1/group-agent/status", headers={"X-API-Key": API_KEY})
    body = response.json()
    assert body["mode"] == "reply" and body["llm"].startswith("test-mode")
    assert body["bridge"]["connected"] is False  # no bridge running in tests
    assert body["chats"][0]["chat_name"] == "La Tour Residents"


# ================================
# REPLYING (test mode LLM)
# ================================

def test_replies_when_addressed_in_allowed_group(client, sent):
    post(client, event("M1", "Hello assistant, can you see this group?"))
    assert len(sent) == 1
    assert sent[0]["chat"] == GROUP and sent[0]["quoted"] == "M1"
    assert "Max Migold Assistant" in sent[0]["text"]
    own = stored(client)[-1]
    assert own["from_me"] == 1 and own["msg_id"] == "OUT1"


def test_silent_when_not_addressed(client, sent):
    post(client, event("M1", "Who is bringing drinks on Saturday?"))
    assert sent == []


def test_never_replies_in_groups_not_allowed(client, sent):
    post(client, event("M1", "assistant hello?", chat=OTHER_GROUP, chat_name="Lagoon Building 2"))
    assert sent == []
    assert len(stored(client, OTHER_GROUP)) == 1  # still seen and stored


def test_listen_mode_never_replies(env, sent, monkeypatch):
    import main_http

    monkeypatch.setenv("GROUP_AGENT_MODE", "listen")
    with TestClient(main_http.app) as c:
        post(c, event("M1", "assistant hello?"))
        assert sent == []
        assert len(stored(c)) == 1


def test_replies_are_spaced_out(client, sent):
    post(client, event("M1", "assistant hello?"))
    post(client, event("M2", "assistant hello again?"))
    assert len(sent) == 1  # second one waits for the 60s gap


# ================================
# REAL (OpenAI-compatible) LLM
# ================================

def test_openai_compatible_llm_reply(client, sent, monkeypatch):
    from group_agent import llm as llm_module
    from group_agent.llm import ChatLLM

    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if "[msg M2]" not in requests[-1]["messages"][-1]["content"]:
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "No reply needed."}}]})
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call_1", "type": "function",
            "function": {"name": "send_reply", "arguments": json.dumps({
                "text": "Sorry about that, Ada. Which block is it? I'll let the facility team know.",
                "reply_to": "M2"})},
        }]}}]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(llm_module.httpx, "AsyncClient",
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    agent(client).llm = ChatLLM("https://llm.example.com/v1", "sk-test", "test-model")

    post(client, event("M1", "Good morning"))
    post(client, event("M2", "There's no water since 6am"))

    assert sent[-1] == {"chat": GROUP, "quoted": "M2",
                        "text": "Sorry about that, Ada. Which block is it? I'll let the facility team know."}
    body = requests[-1]
    assert body["model"] == "test-model" and body["tools"][0]["function"]["name"] == "send_reply"
    transcript = body["messages"][-1]["content"]
    assert "[msg M2]" in transcript and "There's no water since 6am" in transcript
    assert "2348012345678" not in transcript  # phone numbers are never sent to the LLM
    assert body["messages"][0]["role"] == "system" and "never claim to be a human" in body["messages"][0]["content"].lower()


def test_llm_choosing_silence_sends_nothing(client, sent):
    async def silent(messages, tools):
        return {"content": "No reply needed.", "tool_calls": []}

    agent(client).llm.complete = silent
    post(client, event("M1", "Thanks everyone!"))
    assert sent == []


def test_llm_failure_is_retried_on_next_message(client, sent):
    from group_agent.llm import LLMError

    calls = {"n": 0}

    async def flaky(messages, tools):
        calls["n"] += 1
        if calls["n"] == 1:
            raise LLMError("timeout")
        assert "First message" in messages[-1]["content"].split("NEW MESSAGES")[1]  # still treated as new
        return {"content": None, "tool_calls": []}

    agent(client).llm.complete = flaky
    post(client, event("M1", "First message"))
    post(client, event("M2", "Second message"))
    assert calls["n"] == 2


def test_messages_from_before_a_restart_are_not_answered(env, sent):
    import main_http

    with TestClient(main_http.app) as c:
        c.app.state.group_agent.settings.__class__  # noqa: B018 - started once
        c.app.state.group_agent.agent.settings = c.app.state.group_agent.agent.settings.__class__(
            **{**c.app.state.group_agent.agent.settings.__dict__, "mode": "listen"})
        post(c, event("M1", "assistant are you there?"))  # arrives while listening
    with TestClient(main_http.app) as c:
        post(c, event("M2", "Morning all"))
        transcript_holder = {}

        async def capture(messages, tools):
            transcript_holder["t"] = messages[-1]["content"]
            return {"content": None, "tool_calls": []}

        c.app.state.group_agent.agent.llm.complete = capture
        post(c, event("M3", "Anyone else without power?"))
        earlier, new = transcript_holder["t"].split("NEW MESSAGES")
        assert "assistant are you there?" in earlier and "assistant are you there?" not in new


def test_burst_of_messages_gives_one_decision(env, tmp_path):
    from group_agent.agent import GroupAgent
    from group_agent.config import GroupAgentSettings
    from group_agent.store import GroupStore

    settings = GroupAgentSettings.from_env()
    settings = settings.__class__(**{**settings.__dict__, "debounce_seconds": 0.05})
    calls = []

    class CountingLLM:
        name = "counting"

        async def complete(self, messages, tools):
            calls.append(messages[-1]["content"])
            return {"content": None, "tool_calls": []}

    async def run():
        store = GroupStore(str(tmp_path / "burst.db"))
        a = GroupAgent(settings, store, bridge=None, llm=CountingLLM())
        for i in range(3):
            await a.handle_event(event(f"B{i}", f"message {i}"))
        await asyncio.sleep(0.2)
        store.close()

    asyncio.run(run())
    assert len(calls) == 1
    assert all(f"message {i}" in calls[0] for i in range(3))


def test_made_up_reply_to_ids_are_not_quoted(client, sent):
    async def bad_quote(messages, tools):
        if any(m["role"] == "tool" for m in messages):
            return {"content": None, "tool_calls": []}
        return {"content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
            "name": "send_reply", "arguments": json.dumps({"text": "Noted, thanks.", "reply_to": "NOT-A-REAL-ID"})}}]}

    agent(client).llm.complete = bad_quote
    post(client, event("M1", "Gate is broken"))
    assert sent == [{"chat": GROUP, "text": "Noted, thanks.", "quoted": None}]
