---
name: voice-agents
description: Build and operate voice agents on Atoms, Smallest AI's voice-agent platform.
  Use when creating AI agents that make or receive phone calls, placing outbound calls or
  bulk call campaigns via API, attaching knowledge bases to agents, fetching conversation
  logs/transcripts, or embedding a talking voice agent in a web or mobile app.
license: MIT
compatibility: Requires internet access and a Smallest AI API key (SMALLEST_API_KEY).
---

# Smallest AI Voice Agents (Atoms)

Atoms is the voice-agent platform: build agents in the [console](https://app.smallest.ai) or via REST API, then run inbound/outbound calls, campaigns, and web/mobile voice sessions.

> **Setup:** Requires `SMALLEST_API_KEY` — see the `setup-api-key` skill.

**Base URL:** `https://api.smallest.ai/atoms/v1` · Auth: `Authorization: Bearer $SMALLEST_API_KEY`

## Quick Start — create an agent and place a call

### 1. Create an agent (from template is fastest)

```bash
# From a template
curl -X POST "https://api.smallest.ai/atoms/v1/agent/from-template" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"templateId": "<template-id>"}'   # GET /agent-templates to list

# Or blank
curl -X POST "https://api.smallest.ai/atoms/v1/agent" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Support Agent"}'
```

### 2. Place an outbound call

```bash
curl -X POST "https://api.smallest.ai/atoms/v1/conversation/outbound" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "60d0fe4f5311236168a109ca",
    "phoneNumber": "+1234567890"
  }'
```

Response: `{"status": true, "data": {"conversationId": "CALL-..."}}`. Optional `variables` object passes per-call context to the agent. Add header `x-test-call: true` to mark it a test call in logs.

### Python SDK

```python
# pip install smallestai
from smallestai.atoms import AtomsClient

client = AtomsClient()  # reads SMALLEST_API_KEY
agent_id = client.create_agent(create_agent_request={"name": "Support Agent"})
client.start_outbound_call(agent_id=agent_id, phone_number="+1234567890")
```

## ⚠️ The versioning lifecycle — read before editing agents

New agents have **versioning enabled by default**. To change the prompt, `firstMessage`, tools, or runtime config: **fork a draft from the current version → edit → publish → activate.** Guide: https://docs.smallest.ai/atoms/developer-guide/build/agents/versioning-lifecycle

Two traps that cause silent production failures:

1. **Do not use the legacy `PATCH /workflow/{workflowId}`** — it bypasses the version lifecycle; edits aren't captured as a version and may not propagate to live calls.
2. **Before a production call**, fetch `GET /agent/{agentId}` and confirm `_resolvedConfig.firstMessage` (and related fields) match your intent — otherwise the call may play the platform-default greeting instead of your prompt.

## API surface

| Area | Endpoints |
|---|---|
| Agents | `POST /agent`, `GET /agents`, `GET /agent/{id}`, `PATCH` metadata, archive, workflow get/update |
| Templates | `GET /agent-templates`, `POST /agent/from-template` |
| Calls | `POST /conversation/outbound` |
| Campaigns (bulk calling) | create / get / list / delete / start / pause |
| Knowledge bases | `POST /knowledgebase`, get / list, attach to agents |
| Logs | conversation logs by ID, by call IDs, list all |
| Misc | user / org details, prompt scoring |

Full endpoint reference: [references/api-endpoints.md](references/api-endpoints.md)

## Embedding agents in apps

- **Web**: JavaScript WebSocket SDK — mic capture, playback, event streaming: https://docs.smallest.ai/atoms/atoms-platform/integrate/web-socket-sdk
- **Android (Kotlin)**: OkHttp WebSocket + AudioRecord/AudioTrack, min API 24: https://docs.smallest.ai/atoms/atoms-platform/integrate/mobile-integrations/android-kotlin
- **Python real-time agents**: Atoms Agent Crews SDK (nodes, sessions, events, graphs): https://docs.smallest.ai/atoms/developer-guide/get-started/overview
- **Telephony**: [Plivo](https://docs.smallest.ai/atoms/integrations/plivo), [Vonage](https://docs.smallest.ai/atoms/integrations/vonage); also [LiveKit](https://docs.smallest.ai/atoms/integrations/live-kit) and [Pipecat](https://docs.smallest.ai/atoms/integrations/pipecat)

## Error handling

| HTTP | Common causes |
|---|---|
| 400 | Invalid `agentId` / `phoneNumber` (must be E.164) / agent archived / workflow validation errors |
| 401 | Bad `SMALLEST_API_KEY` |
| 403 | Org lacks conversational-agents access (workflow_graph agents) |

Full reference: https://docs.smallest.ai/atoms/atoms-platform/troubleshooting/error-reference

## Links

- Platform quick start (web console): https://docs.smallest.ai/atoms/atoms-platform/get-started/quick-start
- API reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agents/create-a-new-agent
- MCP server for AI assistants: https://docs.smallest.ai/atoms/mcp/getting-started/manual-setup
