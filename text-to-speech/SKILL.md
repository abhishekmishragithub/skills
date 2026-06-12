---
name: text-to-speech
description: Convert text to speech using Smallest AI's Lightning v3.1 and Lightning v3.1 Pro models.
  Use when adding TTS, voiceovers, audio narration, or voice output to an app, generating speech
  in English, Hindi, Spanish, or 9 Indian languages, cloning a voice, streaming low-latency
  speech (~100ms first chunk) for real-time agents, or when premium broadcast-quality voices
  (American, British, Indian accents with English+Hindi code-switching) are needed via the Pro pool.
license: MIT
compatibility: Requires internet access and a Smallest AI API key (SMALLEST_API_KEY).
---

# Smallest AI Text-to-Speech (Lightning)

Generate natural 44.1 kHz speech from text. ~100ms first audio chunk when streaming. Voice cloning supported.

> **Setup:** Requires `SMALLEST_API_KEY` — see the `setup-api-key` skill. Get a key at [app.smallest.ai/dashboard](https://app.smallest.ai/dashboard) → Developer → API Keys.

## Models — always use these

| Model | Languages | Notes |
|---|---|---|
| `lightning_v3.1` (default) | English, Hindi, Marathi, Kannada, Tamil, Bengali, Gujarati, Telugu, Malayalam, Punjabi, Odia, Spanish | Voice cloning supported |
| `lightning_v3.1_pro` | English, Hindi | Premium pool: broadcast-quality voices across American, British, and Indian accents; improved naturalness; dedicated inference capacity. Indian voices code-switch English+Hindi automatically; American/British voices are English-only. Same latency and rate limits as standard. No cloning |

**Choosing:** default to `lightning_v3.1` for multilingual or cloned voices; choose `lightning_v3.1_pro` when voice quality is the priority (narration, branded voice apps, premium agents) and English/Hindi is enough. Both are selected via the `model` body parameter on the same routes (HTTP, SSE, and WebSocket) — there is no separate Pro endpoint.

**Deprecated — never write new code with these:** `lightning-v2`, `lightning-large`, and the old per-model endpoints (`POST /waves/v1/lightning-v3.1/get_speech`). If you find them in existing code, migrate to the unified `/waves/v1/tts` route below.

## Quick Start

### cURL

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{
    "text": "Hello from Smallest AI.",
    "voice_id": "magnus",
    "sample_rate": 24000,
    "output_format": "wav"
  }' --output speech.wav
```

### cURL — Lightning v3.1 Pro (premium voices)

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{
    "text": "Hello from the Lightning v3.1 Pro pool.",
    "voice_id": "meher",
    "model": "lightning_v3.1_pro",
    "language": "en",
    "sample_rate": 24000,
    "output_format": "wav"
  }' --output speech.wav
```

### Python

```python
# pip install requests  (or use the official SDK: pip install smallestai)
import os, requests

response = requests.post(
    "https://api.smallest.ai/waves/v1/tts",
    headers={
        "Authorization": f"Bearer {os.environ['SMALLEST_API_KEY']}",
        "Content-Type": "application/json",
        "Accept": "audio/wav",
    },
    json={
        "text": "Hello from Smallest AI.",
        "voice_id": "magnus",
        "sample_rate": 24000,
        "output_format": "wav",
    },
)
response.raise_for_status()
with open("speech.wav", "wb") as f:
    f.write(response.content)
```

### JavaScript / TypeScript

```typescript
// Works in Node 18+ with built-in fetch (or use: npm install smallestai)
import { writeFileSync } from "node:fs";

const res = await fetch("https://api.smallest.ai/waves/v1/tts", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.SMALLEST_API_KEY}`,
    "Content-Type": "application/json",
    Accept: "audio/wav",
  },
  body: JSON.stringify({
    text: "Hello from Smallest AI.",
    voice_id: "magnus",
    sample_rate: 24000,
    output_format: "wav",
  }),
});
writeFileSync("speech.wav", Buffer.from(await res.arrayBuffer()));
```

## Request Parameters (`POST /waves/v1/tts`)

| Param | Type | Default | Values |
|---|---|---|---|
| `text` | string | required | Text to synthesize |
| `voice_id` | string | required | Catalog voice or cloned voice (`voice_*`) |
| `model` | string | `lightning_v3.1` | `lightning_v3.1` \| `lightning_v3.1_pro` |
| `sample_rate` | int | — | 8000 – 44100 Hz (24000 recommended) |
| `speed` | float | 1.0 | 0.5 – 2.0 |
| `output_format` | string | — | `pcm` \| `mp3` \| `wav` \| `ulaw` \| `alaw` |
| `pronunciation_dicts` | array | — | Per-call pronunciation dictionary IDs |

## Voices

List all voices:

```bash
curl "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices" \
  -H "Authorization: Bearer $SMALLEST_API_KEY"
```

The response is the union of standard and Pro catalogs. Pair Pro voices (e.g. `meher`) with `"model": "lightning_v3.1_pro"`, standard voices (e.g. `magnus`) with the default model. See [references/voices-languages.md](references/voices-languages.md).

## Streaming (low latency)

For playback that starts before synthesis completes (~100ms first chunk), or when text arrives incrementally from an LLM, use `/waves/v1/tts/live` — SSE via HTTP POST, WebSocket via `wss://`. Word-level timestamps available on the WebSocket. See [references/streaming.md](references/streaming.md).

## Voice Cloning

Clone a voice from a short audio sample (`lightning_v3.1` only):
- REST: https://docs.smallest.ai/waves/documentation/voice-cloning/instant-clone-api
- Python SDK: https://docs.smallest.ai/waves/documentation/voice-cloning/instant-clone-python-sdk

Cloned voice IDs are prefixed `voice_*` and are passed as `voice_id` like any catalog voice.

## Common Gotchas

- **Always set `Accept: audio/wav`** on the sync route — omitting it can return an empty or unplayable response.
- **Pair voice IDs with the right model.** The API does not reject mismatched pairings, but a Pro-only voice on `lightning_v3.1` can return wrong audio.
- **Cloned voices work on `lightning_v3.1` only** — not on Pro.
- **Prefer 24000 sample rate** unless you specifically need 44.1 kHz.
- Long text: split into sentences/paragraphs and synthesize per chunk, or use streaming.

## Error Handling

| HTTP | Meaning | Fix |
|---|---|---|
| 400 | Bad request | Check params, voice/model pairing, text length |
| 401 | Unauthorized | Check `SMALLEST_API_KEY` |
| 429 | Rate limited | Back off and retry |
| 5xx | Server error | Retry with exponential backoff |

Full error reference: https://docs.smallest.ai/waves/documentation/troubleshooting/error-reference

## Links

- Docs: https://docs.smallest.ai/waves/documentation/text-to-speech-lightning/overview
- API reference: https://docs.smallest.ai/waves/api-reference/api-reference/text-to-speech/synthesize-speech
- Cookbook: https://docs.smallest.ai/waves/documentation/cookbooks/text-to-speech
- TTS best practices (voice-agent prompting): https://docs.smallest.ai/waves/documentation/best-practices/tts-best-practices
