# Electron Tool Calling — Voice-Agent Patterns

Electron implements the standard OpenAI function-calling API: pass a `tools` array, receive `tool_calls` in the assistant message, post tool results back as `role: "tool"` messages, and the model narrates the answer.

## The filler-phrase pattern

In a voice pipeline (Pulse STT → Electron → Lightning TTS), a tool call normally means dead air: the user hears nothing while the database lookup or webhook runs. Electron's filler-phrase behavior fixes this.

**How it works:** give Electron a system prompt that asks it to acknowledge before tool use. The response then carries both:

- `message.content` — a short conversational filler ("Let me check that for you…") → **send to TTS immediately**
- `message.tool_calls` — the structured calls → **execute concurrently**

By the time the filler finishes playing, the tool result is usually back and the final answer streams in. Perceived latency drops to near zero.

```python
import json

resp = client.chat.completions.create(
    model="electron",
    messages=[
        {"role": "system", "content": "You are a friendly phone agent. Briefly acknowledge out loud before using any tool, like 'Let me check that' or 'One moment'."},
        {"role": "user", "content": "What's the weather in Mumbai?"},
    ],
    tools=tools,
)

msg = resp.choices[0].message
if msg.tool_calls:
    if msg.content:
        speak_via_tts(msg.content)            # 1. mask latency with the filler
    for call in msg.tool_calls:               # 2. run tools meanwhile
        result = run_tool(call.function.name, json.loads(call.function.arguments))
        # 3. post result back and get the narrated answer
        followup = client.chat.completions.create(
            model="electron",
            messages=[*previous_messages, msg,
                      {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}],
            tools=tools,
        )
        speak_via_tts(followup.choices[0].message.content)
```

## Important behavioral notes

- **The filler is prompt-driven, not magic.** Without a system prompt requesting acknowledgment, Electron returns the standard OpenAI shape: `content: null` when `tool_calls` is present. Code defensively — check `msg.content` before speaking it.
- This differs from OpenAI's models, where `content` is `null` alongside `tool_calls` — don't write code that assumes `content` is always `null` (or always present).
- `tool_choice` supports `"auto"`, `"required"`, `"none"`, or a specific function.
- Max **64 tools** per request (400 above that).
- With `stream: true`, tool-call arguments stream incrementally via `response.function_call_arguments` deltas, same as OpenAI.

## Prompting guidance

Full guidance on writing voice-agent system prompts (persona, length discipline, turn-taking):
https://docs.smallest.ai/waves/documentation/llm-electron/tool-function-calling
https://docs.smallest.ai/waves/documentation/llm-electron/best-practices
