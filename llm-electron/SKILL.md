---
name: llm-electron
description: Use Electron, Smallest AI's in-house language model, via OpenAI-compatible chat
  completions. Use when building voice agents or chatbots on Smallest AI, migrating off the
  OpenAI API, needing a fast LLM (sub-300ms TTFT) for real-time/conversational apps, multilingual
  chat in 70 languages with first-class Indic support (Hindi, Tamil, Bengali, Marathi), tool
  calling with voice-friendly filler phrases, or cost-efficient high-volume inference with
  automatic prefix caching.
license: MIT
compatibility: Requires internet access and a Smallest AI API key (SMALLEST_API_KEY). Works with official OpenAI SDKs.
---

# Smallest AI LLM (Electron)

Electron is a **drop-in replacement for the OpenAI Chat Completions API** — same wire format, same SDKs. Sub-300ms time-to-first-token, 32K context, 70 languages with first-class Indic support, automatic prefix caching.

> **Setup:** Requires `SMALLEST_API_KEY` — see the `setup-api-key` skill.

## Quick Start — use the official OpenAI SDK

```bash
pip install openai   # Python
npm install openai   # Node.js
```

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.smallest.ai/waves/v1",
    api_key=os.environ["SMALLEST_API_KEY"],
)

response = client.chat.completions.create(
    model="electron",
    messages=[{"role": "user", "content": "Write one sentence about why the sky is blue."}],
)
print(response.choices[0].message.content)
```

### JavaScript / TypeScript

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api.smallest.ai/waves/v1",
  apiKey: process.env.SMALLEST_API_KEY,
});

const response = await client.chat.completions.create({
  model: "electron",
  messages: [{ role: "user", content: "Write one sentence about why the sky is blue." }],
});
console.log(response.choices[0].message.content);
```

### cURL

```bash
curl -X POST "https://api.smallest.ai/waves/v1/chat/completions" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "electron",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Response is the standard OpenAI chat-completion shape.

## Migrating from OpenAI

Change exactly three strings — everything else (streaming, tool calling, JSON mode, multi-turn) works identically:

1. `base_url` → `https://api.smallest.ai/waves/v1`
2. `api_key` → your Smallest AI key
3. `model` → `"electron"`

Side-by-side diff: https://docs.smallest.ai/waves/documentation/llm-electron/migrate-from-open-ai

## Streaming

Set `"stream": true` for SSE token streaming — same wire format as OpenAI. **Always add `"stream_options": {"include_usage": true}`** so a final usage chunk reports exact tokens served, even if the client disconnects mid-stream.

## Tool calling — the filler-phrase pattern

Electron implements the standard OpenAI `tools` API. Its distinctive feature for voice agents: **with a voice-agent-style system prompt, the model returns a short spoken filler in `content` alongside `tool_calls`** (e.g. "Let me check that for you…"), so a TTS layer can mask tool-call latency.

```python
resp = client.chat.completions.create(
    model="electron",
    messages=[
        {"role": "system", "content": "You are a friendly phone agent. Briefly acknowledge out loud before using any tool, like 'Let me check that' or 'One moment'."},
        {"role": "user", "content": "What's the weather in Mumbai?"},
    ],
    tools=tools,
)
msg = resp.choices[0].message
# msg.content    -> "Let me check that for you!"  (speak this via TTS immediately)
# msg.tool_calls -> [...]                          (run the tool meanwhile)
```

The filler is **prompt-driven, not automatic** — without a system prompt requesting it, Electron returns the standard OpenAI shape (`content: null` with `tool_calls`). Details: [references/tool-calling.md](references/tool-calling.md)

## Prefix caching — automatic, structure prompts for it

Repeated prompt prefixes (system prompts, RAG context, conversation history) are served from cache automatically — faster TTFT and discounted billing. No flag needed. The rule: **stable content first, variable content last.**

```python
messages = [
    {"role": "system", "content": LONG_SYSTEM_PROMPT},     # stable — caches
    {"role": "user", "content": LONG_RAG_CONTEXT_BLOCK},   # stable per session
    {"role": "user", "content": user_question},            # varies — keep last
]
```

Never interpolate per-user values into the start of the system prompt — it breaks the cache for everyone. Audit cache hits via `usage.prompt_tokens_details.cached_tokens` in every response.

## Limits & gotchas

- **Context**: 32,768 tokens combined input + output. Max 200 messages, 64 tools, 4 stop sequences per request.
- **Rejected with 400**: `n > 1` (make separate requests) and `prompt_logprobs`.
- **`response_format`**: `{"type": "text"}` or `{"type": "json_object"}`.
- **Rate limits**: Standard plan 10 RPM / 3 concurrent; Enterprise 200 RPM / 20 concurrent.
- **Debugging**: every response carries an `X-Request-Id` header — include it in support tickets.
- Full parameter passthrough/rejection tables and OpenAI differences: [references/parameters.md](references/parameters.md)

## Building a full voice agent

Electron pairs with Pulse (STT) and Lightning (TTS) for a complete voice agent on one API key — see the `speech-to-text` and `text-to-speech` skills, and the end-to-end cookbook:
https://docs.smallest.ai/waves/documentation/cookbooks/voice-agent-electron-pulse-lightning

## Links

- Overview: https://docs.smallest.ai/waves/documentation/llm-electron/overview
- API reference: https://docs.smallest.ai/waves/api-reference/api-reference/llm-chat-completions/electron-chat-completions
- Model card: https://docs.smallest.ai/waves/model-cards/llm/electron
- Best practices: https://docs.smallest.ai/waves/documentation/llm-electron/best-practices
