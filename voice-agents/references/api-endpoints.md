# Atoms API Endpoints

Base URL: `https://api.smallest.ai/atoms/v1` · All requests: `Authorization: Bearer $SMALLEST_API_KEY`

Each endpoint's full request/response schema is on its docs page (append `.md` for raw markdown).

## Agents

| Method & Path | Purpose | Docs |
|---|---|---|
| `POST /agent` | Create agent (name in body; versioning on by default) | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agents/create-a-new-agent) |
| `GET /agents` | List all agents | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agents/get-all-agents) |
| `GET /agent/{id}` | Get agent — includes `_resolvedConfig` (verify before production calls) | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agents/get-agent-by-id) |
| `PATCH /agent/{id}` | Update agent metadata | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agents/update-agent-metadata) |
| — | Archive / unarchive agent | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agents/delete-agent) |
| — | Get / update agent workflow (prefer the versioned drafts flow) | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agents/get-agent-workflow) |

## Agent templates

| Endpoint | Docs |
|---|---|
| `GET /agent-templates` | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agent-templates/get-agent-templates) |
| `POST /agent/from-template` | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/agent-templates/create-agent-from-template) |

## Calls

| Endpoint | Notes | Docs |
|---|---|---|
| `POST /conversation/outbound` | Body: `agentId`, `phoneNumber` (E.164), optional `variables`. Header `x-test-call: true` for test calls. Returns `conversationId` | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/calls/start-an-outbound-call) |

## Campaigns (bulk outbound)

Create, retrieve (one/all), delete, start/resume, pause:
https://docs.smallest.ai/atoms/api-reference/api-reference/campaigns/create-a-campaign (sibling pages for the rest)

## Knowledge bases

| Endpoint | Docs |
|---|---|
| `POST /knowledgebase` | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/knowledge-base/create-a-knowledge-base) |
| `GET /knowledgebase` (all) / `GET /knowledgebase/{id}` | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/knowledge-base/get-all-knowledge-bases) |

## Conversation logs

| Endpoint | Docs |
|---|---|
| Get all conversation logs | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/logs/get-all-conversation-logs) |
| Search logs by call IDs | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/logs/search-conversation-logs-by-call-i-ds) |
| Get log by ID | [link](https://docs.smallest.ai/atoms/api-reference/api-reference/logs/get-conversation-log-by-id) |

## Account

- `GET` user details: https://docs.smallest.ai/atoms/api-reference/api-reference/user/get-user-details
- `GET` organization details: https://docs.smallest.ai/atoms/api-reference/api-reference/organization/get-organization-details
- Prompt scoring: https://docs.smallest.ai/atoms/api-reference/api-reference/prompt-scoring/score-a-prompt

## Full index

Complete, always-current endpoint list: https://docs.smallest.ai/atoms/llms.txt
