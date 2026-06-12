# Voices & Languages

## Listing voices

```bash
curl "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices" \
  -H "Authorization: Bearer $SMALLEST_API_KEY"
```

The response is the **union** of the standard Lightning v3.1 catalog and the Lightning v3.1 Pro catalog — there is no per-voice "Pro" flag in the response. The canonical per-pool lists live on the model cards:

- Lightning v3.1 voices: https://docs.smallest.ai/waves/model-cards/text-to-speech/lightning-v-3-1
- Lightning v3.1 Pro voices: https://docs.smallest.ai/waves/model-cards/text-to-speech/lightning-v-3-1-pro

**Always pair the voice with its pool**: Pro voices (e.g. `meher`) require `"model": "lightning_v3.1_pro"`; standard voices (e.g. `magnus`) use the default `lightning_v3.1`. Mismatches are not rejected by the API but can produce wrong audio.

## Languages

### Lightning v3.1 (12 languages)

English, Hindi, Marathi, Kannada, Tamil, Bengali, Gujarati, Telugu, Malayalam, Punjabi, Odia, Spanish — plus auto-detect.

### Lightning v3.1 Pro

English and Hindi. The Pro catalog is curated across **American, British, and Indian accents**:
- **Indian voices** code-switch English+Hindi automatically (mixed languages in one utterance work naturally)
- **American and British voices** are English-only

Pro runs on dedicated inference capacity with the same latency, concurrency, and rate limits as standard Lightning v3.1 — the difference is voice quality and the catalog. On Atoms voice agents, Pro voices appear under the **Pro** filter chip in the voice picker and route automatically.

Language codes are [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) two-letter codes (`en`, `hi`, `mr`, `kn`, `ta`, `bn`, `gu`, `te`, `ml`, `pa`, `or`, `es`).

## Picking a voice

Full guide (filter by language and accent, find voice IDs): https://docs.smallest.ai/waves/documentation/text-to-speech-lightning/voices-languages

## Pronunciation dictionaries

Control how specific words are pronounced (names, brands, acronyms) via per-call `pronunciation_dicts`:
https://docs.smallest.ai/waves/documentation/text-to-speech-lightning/pronunciation-dictionaries
