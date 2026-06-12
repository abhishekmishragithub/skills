---
name: speech-to-speech
description: Build realtime voice conversations with Hydra, Smallest AI's full-duplex
  speech-to-speech model. Use when building voice assistants or phone agents that need
  audio-in/audio-out over one WebSocket (no STT→LLM→TTS pipeline), realtime conversational
  AI with barge-in/interruption handling, or as an alternative to the OpenAI Realtime API.
  English only. Sub-second voice-to-voice latency with tool calling.
license: MIT
compatibility: Requires internet access and a Smallest AI API key (SMALLEST_API_KEY). WebSocket client required.
---

# Smallest AI Speech-to-Speech (Hydra)

Hydra is a **realtime, full-duplex speech-to-speech model**: stream microphone audio in, get synthesized speech back, on a single WebSocket. Turn-taking and barge-in are handled server-side. No transcript on the wire — audio is the payload. If you've used the OpenAI Realtime API, Hydra fills the same role on the Smallest AI stack.

> **Setup:** Requires `SMALLEST_API_KEY` — see the `setup-api-key` skill. English only today.

## Endpoint

```
wss://api.smallest.ai/waves/v1/s2s?model=hydra&api_key=<SMALLEST_API_KEY>
```

- `model=hydra` is required. All frames are **JSON text frames** (UTF-8) — binary frames are not used.
- Auth happens at the handshake: a bad key returns **HTTP 401 before the socket opens** (no close code to catch).
- **Browser apps: never ship the raw key** — mint a short-lived token server-side.
- Idle timeout: ~30 seconds without audio.

## Session flow

1. Connect → server sends `session.created`
2. Send **exactly one** `session.configure` (persona, voice, tools) → server echoes `session.configured`
3. Stream mic audio continuously via `input_audio_buffer.append` — **no commit/end-of-turn signal; Hydra detects turn boundaries itself**
4. Receive `input_audio_buffer.speech_started` / `speech_stopped`, then `response.created`, streamed `response.output_audio.delta` chunks, `response.output_audio.done`, `response.done`
5. User speaks over the model → in-flight response auto-cancels (`status: "cancelled"`, `reason: "interrupted"`) — handle by flushing your playback buffer

### `session.configure` (send once, right after `session.created`)

```json
{
  "type": "session.configure",
  "session": {
    "instructions": "You are a warm, concise voice assistant. Reply in one short sentence.",
    "voice": "wren",
    "tools": [],
    "generate_initial_response": false
  }
}
```

| Field | Notes |
|---|---|
| `instructions` | System prompt — see [prompting guide](https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/prompting-voice-agents) |
| `voice` | `wren`, `sloane`, `marlowe`, `reed`, `knox`, `tate` |
| `tools` | OpenAI-style function schemas |
| `generate_initial_response` | `true` = model speaks first |

### Minimal Python client

```python
# pip install websockets
import asyncio, base64, json, os, wave
import websockets

URL = f"wss://api.smallest.ai/waves/v1/s2s?model=hydra&api_key={os.environ['SMALLEST_API_KEY']}"

async def main():
    async with websockets.connect(URL, max_size=None) as ws:
        async for raw in ws:
            event = json.loads(raw)
            if event["type"] == "session.created":
                await ws.send(json.dumps({
                    "type": "session.configure",
                    "session": {"instructions": "Be brief and friendly.", "voice": "wren"},
                }))
            elif event["type"] == "session.configured":
                w = wave.open("input_16k_mono.wav", "rb")
                while pcm := w.readframes(320):     # 20ms chunks at 16 kHz
                    await ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(pcm).decode(),
                    }))
            elif event["type"] == "response.output_audio.delta":
                play(base64.b64decode(event["delta"]))   # PCM16 chunks

asyncio.run(main())
```

## Audio format — Hydra is strict

| | Input (client → server) |
|---|---|
| Codec | PCM16, little-endian, **mono** |
| Sample rate | **16,000 Hz** |
| Encoding | base64 inside `input_audio_buffer.append.audio` |
| Chunk size | **20–40 ms** (640–1280 bytes) — smaller adds overhead, larger makes barge-in sluggish |

Output sample rate is negotiated at handshake. Wrong format = `invalid_audio` errors or distorted playback. Browser mic wiring (AudioWorklet at 16 kHz): https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/audio-i-o

## Critical gotchas

- **`session.configure` silently ignores unknown fields** — a typo like `instuctions` ships the default persona with no error. Validate keys client-side. (`session.update` is stricter and rejects unknown fields.)
- **Unknown `voice` values silently fall back to default** — validate against the six voices client-side.
- **Mid-session updates**: only `tools` can change via `session.update`; persona, voice, and audio format are frozen at handshake — reconnect to change them.
- **Handle interruption**: on `reason: "interrupted"`, stop playback immediately and discard buffered audio, or the user hears the model talk over them.

## Tool calling

Declare tools in `session.configure`; arguments stream via `response.function_call_arguments` deltas; post results back and Hydra narrates the answer: https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/tool-calling

## Errors & reconnection

Error frames are diagnostic — the session stays usable unless a close follows. Reference and reconnection strategy: https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/errors-reconnection

## Links

- Overview: https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/overview
- Quickstart (browser reference client): https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/quickstart
- Sessions: https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/managing-sessions
- Turn detection & barge-in: https://docs.smallest.ai/waves/documentation/speech-to-speech-hydra/turn-detection-barge-in
- Model card: https://docs.smallest.ai/waves/model-cards/speech-to-speech/hydra
