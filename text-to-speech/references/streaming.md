# Lightning TTS Streaming

Two transports on the same URL — `https://api.smallest.ai/waves/v1/tts/live`:

| Transport | Use when |
|---|---|
| **SSE** (`POST https://.../tts/live`) | You have the full text up front and want playback to start early (long passages, live narration) |
| **WebSocket** (`wss://.../tts/live`) | Text arrives incrementally — LLM token streams, conversational agents |

Request body is identical to the sync `/waves/v1/tts` route (`text`, `voice_id`, `model`, `sample_rate`, `speed`, `output_format`).

## SSE

```bash
curl -N -X POST "https://api.smallest.ai/waves/v1/tts/live" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "A longer passage to narrate...", "voice_id": "magnus", "sample_rate": 24000}'
```

Response is `text/event-stream`:
- Each chunk: `event: audio` + `data: {"audio": "<base64-pcm>"}`
- Final frame: `data: {"done": true}`

Decode each chunk's `audio` field from base64 and feed the raw PCM to your audio pipeline (browser `MediaSource`, ffmpeg pipe, PCM player).

## WebSocket

```python
# pip install websockets
import asyncio, base64, json, os
import websockets

API_KEY = os.environ["SMALLEST_API_KEY"]
WS_URL = "wss://api.smallest.ai/waves/v1/tts/live"

async def stream_tts(text: str):
    async with websockets.connect(
        WS_URL, additional_headers={"Authorization": f"Bearer {API_KEY}"}
    ) as ws:
        await ws.send(json.dumps({
            "text": text,
            "voice_id": "magnus",
            "sample_rate": 24000,
        }))
        pcm = b""
        async for message in ws:
            frame = json.loads(message)
            if frame.get("data", {}).get("audio"):
                pcm += base64.b64decode(frame["data"]["audio"])
            if frame.get("status") == "complete":
                break
        return pcm

asyncio.run(stream_tts("Hello, streaming world."))
```

## Word-level timestamps (WebSocket only)

Pass `"word_timestamps": true` in the WebSocket request to receive per-word timing events (`status: "word_timestamp"`) interleaved with audio chunks — for live captions, karaoke highlighting, avatar lip-sync. Words are returned verbatim from input (`"$100"` stays `"$100"`). Supported on English + Hindi base-queue voices.

Reference: https://docs.smallest.ai/waves/documentation/text-to-speech-lightning/word-timestamps

## Choosing a transport

Full decision guide: https://docs.smallest.ai/waves/documentation/text-to-speech-lightning/http-vs-streaming-vs-web-sockets
