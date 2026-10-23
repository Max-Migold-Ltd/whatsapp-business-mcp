# WhatsApp Group Agent

A dedicated WhatsApp number joins residents' groups as **Max Migold Assistant**. It reads every
message and, using an LLM you choose (any OpenAI-compatible API), replies when needed.

```
Residents' groups ──▶ dedicated phone number, linked like WhatsApp Web
                        │
                        ▼
                wa_bridge/ (Node.js, Baileys)  ──every message──▶  group_agent/ (Python, in main_http.py)
                        ▲                                            ├─ stores it (group_messages table)
                        └──────────── reply ◀── send_reply tool ◀───┴─ asks the LLM: reply or stay silent?
```

**Status: milestone 1 - see messages and reply.** Ticket logging to Excel, "done" detection and
feedback/NPS come next, as further LLM tools.

> **Risk:** WhatsApp does not permit automating a normal WhatsApp account this way; the number can
> be banned. Use a dedicated number (never the official support line), warm it up by normal use first,
> and keep replies sparse.

## How it decides

- Messages in a group are batched for `GROUP_AGENT_DEBOUNCE_SECONDS` (default 6), so a burst gets one decision.
- The LLM sees the last `GROUP_AGENT_HISTORY` messages (default 30) - earlier ones marked as context, the
  rest as NEW - plus the instructions in [group_agent/prompt.md](group_agent/prompt.md). It replies by calling
  the `send_reply` tool, or stays silent by calling nothing.
- At most one reply per decision, and at least `GROUP_AGENT_MIN_REPLY_GAP_SECONDS` (default 60) between
  replies in the same group.
- **Only names are sent to the LLM** - never phone numbers.
- It identifies itself as an AI assistant and never claims to be human (in the prompt).

## Safety switches

| Setting | Effect |
|---|---|
| `GROUP_AGENT_ENABLED=false` | Off entirely; the bridge is not started |
| `GROUP_AGENT_MODE=listen` | Reads and stores every message, **never replies** |
| `GROUP_AGENT_MODE=reply` + `GROUP_AGENT_REPLY_CHATS=Test Group` | Replies only in the listed groups (names or ids; `*` = all) |
| `LLM_BASE_URL` empty | Test mode: replies only when someone writes "assistant", with a fixed message |

## Setup

1. **The phone:** a dedicated SIM with WhatsApp (or WhatsApp Business) installed and used normally for
   a week or two. Add it to the groups.
2. **Settings** (in Depot's environment variables):
   ```
   GROUP_AGENT_ENABLED=true
   GROUP_AGENT_MODE=listen
   BRIDGE_SECRET=<long random string>
   LLM_BASE_URL=https://api.your-provider.com/v1
   LLM_API_KEY=<key>
   LLM_MODEL=<model name>
   ```
3. **Deploy**, then link the phone - either:
   - **Code:** `POST /api/v1/group-agent/pair` with `{"phone": "2348012345678"}` (header `X-API-Key`) returns an
     8-character code; on the phone: WhatsApp → Settings → Linked devices → Link a device →
     **Link with phone number instead** → enter the code.
   - **QR:** `GET /api/v1/group-agent/qr` (header `X-API-Key`) returns the QR image to scan from Linked devices.
4. Check `GET /api/v1/group-agent/status`: `bridge.connected` should be `true`, and `chats` fills up as messages arrive.
5. To test replies, create a small test group, then set `GROUP_AGENT_MODE=reply` and
   `GROUP_AGENT_REPLY_CHATS=<test group name>`.

**Staying linked:** with `DATABASE_URL` set (as on Depot), the linked-device session is stored in the
PostgreSQL table `wa_auth`, so the phone stays linked across redeploys. Treat that table as a password:
anyone with it can act as the WhatsApp number. If the phone removes the linked device, the session is cleared
automatically and a new pairing code or QR can be requested.

## Endpoints (all need `X-API-Key`)

| Endpoint | Returns |
|---|---|
| `GET /api/v1/group-agent/status` | Mode, LLM in use, bridge connection, message counts per group |
| `POST /api/v1/group-agent/pair` | Pairing code for "Link with phone number" |
| `GET /api/v1/group-agent/qr` | Login QR code (PNG) |
| `GET /api/v1/group-agent/groups` | Groups the number is in, with member counts |
| `GET /api/v1/group-agent/messages?chat=<id>` | Stored messages, newest first |
