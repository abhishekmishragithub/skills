# Pulse Real-time Transcription (WebSocket)

64ms time-to-first-transcript. For live conversations, voice assistants, and streaming pipelines.

## Endpoint

```
wss://api.smallest.ai/waves/v1/stt/live?model=pulse
```

Common query parameters: `language`, `encoding` (e.g. `linear16`), `sample_rate` (e.g. `16000`), `word_timestamps`. Pulse Pro is **not** available on this endpoint (returns 400).

## Connect

```javascript
const url = new URL("wss://api.smallest.ai/waves/v1/stt/live?model=pulse");
url.searchParams.append("language", "en");
url.searchParams.append("encoding", "linear16");
url.searchParams.append("sample_rate", "16000");
url.searchParams.append("word_timestamps", "true");

const ws = new WebSocket(url.toString(), {
  headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
});

ws.onopen = () => {
  // stream binary audio chunks (a few KB each) as they're captured
};
ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log(result); // incremental transcripts
};
```

Python and browser examples: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/realtime-web-socket/code-examples

## Key docs

- Quickstart: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/realtime-web-socket/quickstart
- Response format: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/realtime-web-socket/response-format
- Audio specifications: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/realtime-web-socket/audio-formats
- Best practices (latency/accuracy tuning): https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/realtime-web-socket/best-practices

## Real-time-specific controls

- **End-of-utterance timeout** — how long Pulse waits after speech stops before finalizing: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/end-of-utterance-timeout
- **Finalize control** — manual finalization via `finalize_on_words` / `max_words`: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/finalize-control
- **Punctuation formatting** in live transcripts: https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/punctuation-formatting
- **Inverse text normalization** (spoken → written form): https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/features/inverse-text-normalization
