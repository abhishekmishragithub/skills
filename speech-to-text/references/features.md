# Pulse STT Features

All features are enabled via query parameters on `POST /waves/v1/stt/` or the `wss://.../stt/live` connection URL.

| Feature | What it does | Docs |
|---|---|---|
| Word timestamps (`word_timestamps=true`) | Per-word start/end timing | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/word-timestamps |
| Speaker diarization | Turn-by-turn speaker IDs on words and utterances | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/diarization |
| Utterances | Sentence-level segments with speaker labels | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/utterances |
| Language detection | Auto-detect across 38 languages | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/language-detection |
| PII / PCI redaction | Auto-redact sensitive info from transcripts | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/redaction |
| Emotion detection | Per-emotion confidence scores | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/emotion-detection |
| Gender detection | Speaker gender prediction | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/gender-detection |
| Keyword boosting | Boost domain words/phrases for correct recognition | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/keyword-boosting |
| Punctuation formatting | Control punctuation/capitalization in real time | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/punctuation-formatting |
| Inverse text normalization | Spoken form → written form ("five dollars" → "$5") | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/inverse-text-normalization |
| End-of-utterance timeout | Tune finalization delay after speech ends (realtime) | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/end-of-utterance-timeout |
| Finalize control | Manual finalization via `finalize_on_words` / `max_words` (realtime) | https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/finalize-control |

Full pre-recorded feature list: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/pre-recorded/features
Full realtime feature list: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/realtime-web-socket/features
