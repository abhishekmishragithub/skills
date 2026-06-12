---
name: setup-api-key
description: Obtain and configure a Smallest AI API key (SMALLEST_API_KEY). Use when setting up
  Smallest AI for the first time, when API calls return 401 Unauthorized, or when the user asks
  where to get a Smallest AI / Waves / Atoms API key.
license: MIT
compatibility: Requires a Smallest AI account.
---

# Smallest AI API Key Setup

All Smallest AI APIs (TTS, STT, LLM, S2S) authenticate with a Bearer token from one API key.

## Get a key

1. Sign in at [app.smallest.ai/dashboard](https://app.smallest.ai/dashboard)
2. In the left sidebar under **Developer**, click **API Keys**
3. Click **Create API Key** (top-right), name it (e.g. `my-tts-app`), confirm
4. **Copy it immediately** — the key is shown only once at creation

## Configure

```bash
export SMALLEST_API_KEY="your-api-key-here"
```

Add to `~/.bashrc` / `~/.zshrc` to persist, or to your project's `.env` file (never commit it).

## Use

Every request takes the key in the `Authorization` header:

```
Authorization: Bearer $SMALLEST_API_KEY
```

Verify it works:

```bash
curl -X POST "https://api.smallest.ai/waves/v1/tts" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: audio/wav" \
  -d '{"text": "Authentication test", "voice_id": "magnus", "output_format": "wav"}' \
  --output test.wav && file test.wav
```

A 401 response means the key is missing, mistyped, or revoked.

## Notes

- Requests are geo-routed automatically to the nearest cluster (Mumbai or Oregon) — no configuration needed.
- Concurrency and rate limits: https://docs.smallest.ai/waves/api-reference/api-references/concurrency-and-limits
- Full auth docs: https://docs.smallest.ai/waves/documentation/getting-started/authentication
