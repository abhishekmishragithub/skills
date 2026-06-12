---
name: speech-to-text
description: Transcribe audio to text using Smallest AI's Pulse and Pulse Pro models.
  Use when transcribing audio files, call recordings, voicemails, or podcasts, building
  real-time transcription or voice assistants, or when speaker diarization, word timestamps,
  emotion detection, or PII redaction is needed. Pulse supports 38 languages with 64ms TTFT
  streaming; Pulse Pro is leaderboard-ranked English STT.
license: MIT
compatibility: Requires internet access and a Smallest AI API key (SMALLEST_API_KEY).
---

# Smallest AI Speech-to-Text (Pulse)

Transcribe pre-recorded audio over HTTP or live audio over WebSocket (64ms time-to-first-transcript).

> **Setup:** Requires `SMALLEST_API_KEY` — see the `setup-api-key` skill.

## Models — pick by use case

| Model | Languages | Transport | Best for |
|---|---|---|---|
| `pulse` | 38 languages, auto-detect | HTTP + WebSocket streaming | Multilingual, real-time (64ms TTFT), audio-by-URL |
| `pulse-pro` | English only | HTTP only (pre-recorded) | Maximum accuracy — tied #2 on the public Open ASR Leaderboard (5.42% avg WER), ahead of ElevenLabs Scribe v2, AssemblyAI Universal-3 Pro, and every Whisper variant |

**Choosing:** use `pulse-pro` for pre-recorded English files where accuracy matters most (call recordings, meetings, voicemail analytics); use `pulse` for live streaming, any non-English audio, or the audio-by-URL flow. The `model` query parameter is **required** — requests without it return 400.

## Quick Start — Pre-recorded (`POST /waves/v1/stt/`)

### cURL

```bash
curl -X POST "https://api.smallest.ai/waves/v1/stt/?model=pulse-pro&language=en&word_timestamps=true" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@./call.wav"
```

### Python

```python
import os, requests

with open("./call.wav", "rb") as f:
    audio = f.read()

r = requests.post(
    "https://api.smallest.ai/waves/v1/stt/",
    params={"model": "pulse-pro", "language": "en", "word_timestamps": "true"},
    headers={
        "Authorization": f"Bearer {os.environ['SMALLEST_API_KEY']}",
        "Content-Type": "application/octet-stream",
    },
    data=audio,
)
r.raise_for_status()
print(r.json()["transcription"])
```

### JavaScript / TypeScript

```typescript
import { readFileSync } from "node:fs";

const audio = readFileSync("./call.wav");
const params = new URLSearchParams({ model: "pulse-pro", language: "en", word_timestamps: "true" });

const res = await fetch(`https://api.smallest.ai/waves/v1/stt/?${params}`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.SMALLEST_API_KEY}`,
    "Content-Type": "application/octet-stream",
  },
  body: audio,
});
console.log((await res.json()).transcription);
```

### Audio by URL (`pulse` only)

```bash
curl -X POST "https://api.smallest.ai/waves/v1/stt/?model=pulse&language=en" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-bucket.s3.amazonaws.com/call.wav"}'
```

### Response shape

```json
{
  "status": "success",
  "transcription": "Hi, how are you doing? ...",
  "words": [],
  "language": "en",
  "metadata": { "duration": 17.643, "processing_time_ms": 482.21, "rtfx": 36.6, "num_chunks": 1 },
  "request_id": "8c355f4d-bd45-48ee-aa83-d00e4670f6bb"
}
```

With `word_timestamps=true`, `words` contains per-word `{word, start, end}` entries; diarization adds speaker labels.

### Async via webhook (`pulse-pro` only — long files)

Add `webhook_url=https://your.app/cb` as a query param. Returns `200 {"status": "processing", "request_id": "..."}` immediately; the webhook receives the full transcription. Docs: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/pre-recorded/webhooks

## Real-time streaming (`WSS /waves/v1/stt/live`)

```
wss://api.smallest.ai/waves/v1/stt/live?model=pulse&language=en&encoding=linear16&sample_rate=16000&word_timestamps=true
```

Authenticate with the `Authorization: Bearer` header on the upgrade request, stream binary audio chunks, receive incremental transcripts. **Pulse Pro has no streaming worker** — `model=pulse-pro` on this endpoint returns 400. Full guide: [references/realtime.md](references/realtime.md)

## Features (query parameters)

Speaker diarization, word timestamps, sentence-level utterances, emotion detection, gender detection, PII/PCI redaction, keyword boosting, punctuation formatting, language detection, inverse text normalization, end-of-utterance timeout, finalize control. See [references/features.md](references/features.md).

## Common Gotchas

- **`model` query param is required** — missing/invalid values return 400.
- **Pulse Pro is English only** — pass `language=en`; other codes are accepted but produce unpredictable output.
- **Pulse Pro does not support audio-by-URL** — raw bytes only.
- **Async webhook mode is Pulse Pro only** — `pulse` runs sync on the HTTP endpoint.
- **Max payload 250 MB** (413 above that) — compress to mono 16 kHz PCM if close; quality is unaffected.
- Supported formats and recommendations: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/pre-recorded/audio-formats

## Error Handling

| HTTP | Meaning | Fix |
|---|---|---|
| 400 | Bad/missing `model`, bad params | Check query params |
| 401 | Unauthorized | Check `SMALLEST_API_KEY` |
| 413 | Payload too large | Stay under 250 MB; compress to mono 16 kHz |
| 429 | Rate limited | Back off and retry |

Full error reference: https://docs.smallest.ai/waves/documentation/troubleshooting/error-reference

## Links

- Overview: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/overview
- API reference: https://docs.smallest.ai/waves/api-reference/api-reference/speech-to-text/transcribe
- Cookbook: https://docs.smallest.ai/waves/documentation/cookbooks/speech-to-text
- Model cards: https://docs.smallest.ai/waves/model-cards/speech-to-text/pulse and https://docs.smallest.ai/waves/model-cards/speech-to-text/pulse-pro
