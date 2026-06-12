# Electron Parameters Reference

Endpoint: `POST https://api.smallest.ai/waves/v1/chat/completions` · `model: "electron"`

## Passthrough — standard OpenAI semantics

| Field | Notes |
|---|---|
| `model` | Must be `"electron"` |
| `messages` | Roles: `system`, `user`, `assistant`, `tool`. **Max 200 per request** |
| `temperature` | `0.0` and up |
| `top_p` | `0.0`–`1.0` |
| `max_tokens` | Combined input + output ceiling: **32,768 tokens** |
| `stream` | SSE when `true` |
| `stream_options.include_usage` | Strongly recommended with streaming — final usage chunk |
| `stop` | String or array (max 4) |
| `seed` | Best-effort determinism |
| `response_format` | `{"type":"text"}` (default) or `{"type":"json_object"}` |
| `tools` | **Max 64 entries** |
| `tool_choice` | `"auto"` \| `"required"` \| `"none"` \| specific function |
| `logit_bias`, `logprobs`, `top_logprobs` | Standard (top_logprobs 0–20, requires logprobs) |
| `presence_penalty`, `frequency_penalty` | `-2.0` to `2.0` |
| `user` | Opaque identifier for your logs |

Unrecognized fields are accepted and forwarded; the model may ignore them.

## Rejected — HTTP 400 `invalid_request_error`

| Field | Why |
|---|---|
| `n > 1` | Use separate requests |
| `prompt_logprobs` | Not supported |

## Hard limits (400 when exceeded)

| Limit | Value |
|---|---|
| Messages per request | 200 |
| Tools per request | 64 |
| Combined context (input + output) | 32,768 tokens |
| Stop sequences | 4 |
| top_logprobs | 20 |

## Electron extensions to the response

| Path | Description |
|---|---|
| `usage.prompt_tokens_details.cached_tokens` | Input tokens served from prefix cache (billed at discounted rate) |
| HTTP header `X-Request-Id` | Unique request ID — echo in support tickets |
| `content` alongside `tool_calls` | Often a voice filler phrase (prompt-driven); OpenAI returns `null` here |

## Differences from OpenAI at a glance

| | OpenAI | Electron |
|---|---|---|
| Endpoint path | `/v1/chat/completions` | `/waves/v1/chat/completions` |
| `model` | `"gpt-4o"` etc. | `"electron"` |
| Auth | `Bearer sk-…` (OpenAI key) | `Bearer` Smallest API key |
| `n` | Up to 128 | Rejected (`n=1` only) |
| `content` with tool calls | `null` | Often a filler phrase |

## Rate limits

| Plan | RPM | Concurrent |
|---|---|---|
| Standard | 10 | 3 |
| Enterprise | 200 | 20 |

Higher limits: https://smallest.ai/contact

Full reference: https://docs.smallest.ai/waves/documentation/llm-electron/supported-parameters
