# Pulse real-time transcription (WebSocket)

Streaming transcription over a single WebSocket. 64 ms to first transcript.

Building a voice agent, where turns have to be committed to an LLM? Use the `voice-agent-stt` skill. This page covers the transport; that one covers turn handling, the framework plugins, and the failure modes specific to agents.

## Endpoint

```
wss://api.smallest.ai/waves/v1/stt/live?model=pulse
```

Two streaming models:

- `model=pulse`, 38 languages. The default choice, and the one to use for voice agents.
- `model=pulse-2`, English only. Choose it when you specifically want per-utterance emotion and gender, or its built-in end-of-turn detection. See the [Pulse 2.0 model card](https://docs.smallest.ai/model-cards/speech-to-text/pulse-2-0).

`pulse-pro` is pre-recorded only and is rejected with HTTP 400 before the WebSocket upgrades.

`api.smallest.ai` routes to the nearest region. Some languages are served from one region only, so for those use the regional host directly: `wss://api.us.smallest.ai/...` for `zh`, `yue`, `ja`, `ko`, `multi-asian`, and `wss://api.india.smallest.ai/...` for `ta`, `te`, `kn`, `ml`, `multi-south-indic`.

## Authentication

| Client | Form |
|---|---|
| Server-side | `Authorization: Bearer $SMALLEST_API_KEY` |
| Mobile or native, which can set headers | `Authorization: Bearer <short-lived token>` |
| Browser, using `new WebSocket()` | `?api_key=<short-lived token>` in the URL |

A browser cannot set request headers on a WebSocket. Passing the credential as a subprotocol returns 401. Mint a short-lived token on your backend with `POST /waves/v1/auth/token` and hand that to the page; a token is valid only in the region that minted it.

## Audio

Send **binary** frames. Do not base64-encode. Chunks of 20 to 40 ms.

`sample_rate` and `encoding` must match the audio you actually send. A mismatch produces a garbled transcript with no error. Accepted encodings are `linear16`, `linear32`, `alaw`, `mulaw`, `opus`, `ogg_opus`; rates are 8000, 16000, 22050, 24000, 44100, 48000.

## Connect

Node, using the `ws` package:

```javascript
import WebSocket from "ws";

const params = new URLSearchParams({
  model: "pulse",
  language: "en",
  encoding: "linear16",
  sample_rate: "16000",
  word_timestamps: "true",
});

const ws = new WebSocket(`wss://api.smallest.ai/waves/v1/stt/live?${params}`, {
  headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
});

ws.on("open", () => {
  // send binary PCM in 20-40 ms chunks as it is captured
});

ws.on("message", (data, isBinary) => {
  if (isBinary) return;
  const m = JSON.parse(data.toString());
  if (m.type === "error") return console.error(m);
  if (m.is_final && m.transcript.trim()) console.log("final:", m.transcript);
});
```

In a browser the `headers` option does not exist, so put the token in the URL instead:

```javascript
const ws = new WebSocket(`wss://api.smallest.ai/waves/v1/stt/live?${params}&api_key=${token}`);
```

Python and browser examples: https://docs.smallest.ai/models/speech-to-text/realtime-web-socket/code-examples

## What comes back

Transcription messages carry `transcript` (and the identical `transcription`), `is_final`, `is_last`, `session_id`, and on finals `language`.

```json
{"type":"transcription","transcript":"Please transfer","is_final":false,"is_last":false,"session_id":"..."}
{"type":"transcription","transcript":" Please transfer 25,000 rupees.","is_final":true,"is_last":false,"language":"en","session_id":"..."}
```

Three rules that matter:

- **Use a final, never a partial.** Partials are revised until the final arrives.
- **A final with `is_last: true` can still carry text.** If you close the stream while speech is still buffered, the last utterance arrives on that message and nowhere else. Do not skip it.
- **A final with an empty transcript is normal.** It happens at shutdown, and after a `finalize` sent when nothing was pending. It is not an error.

Transcripts may begin with a space, and after a mid-sentence split with a period. Trim both.

Other message types on the same socket: `speech_started` and `speech_ended` when `vad_events=true`, `pong` in reply to a keep-alive, `{"type":"error"}` for a rejected parameter or a region-gated language, and `{"status":"info","type":"server_shutdown"}` about a minute before a deploy closes the connection with code 1012. Note the last one carries `status`, not `type: "error"`, so a handler that branches only on errors misses it.

## Control messages

JSON text frames on the same socket.

| Message | Effect |
|---|---|
| `{"type":"finalize"}` | Forces an immediate final for the audio buffered so far. The socket stays open. The response carries `from_finalize: true`. |
| `{"type":"close_stream"}` | Flushes, emits the terminal final with `is_last: true`, then closes. |
| `{"type":"ping"}` | Keep-alive. The server replies `{"type":"pong"}`. Send one every 20 to 30 s during silence. |

There is no `{"type":"end"}`. An unrecognised JSON type is treated as audio, so the session stays open until it times out.

Always send `close_stream` and wait for the `is_last` message before dropping the socket, or you lose whatever was still buffered.

## Which options actually return data on streaming

Verified against the live endpoint. Several parameters are accepted on the connection but produce nothing on this surface.

| Parameter | On streaming |
|---|---|
| `word_timestamps` | Returns `words[]` with `start`, `end`, `confidence` |
| `sentence_timestamps` | Returns `utterances[]` |
| `diarize` | Returns `diarization_segments[]`, and a `speaker` on each word |
| `keywords` | Applies |
| `redact_pii`, `redact_pci` | Applies to the transcript text. The `redacted_entities` array is documented but does not arrive |
| `emotion_detection`, `gender_detection` | Nothing on `model=pulse`. These are Pulse 2.0 features, on by default there |

## Pulse 2.0

`model=pulse-2` is English-only. It closes finals on turn boundaries decided by a built-in model rather than a silence window, so finals are fewer and longer, and there are no endpointing knobs to tune: `eou_timeout_ms` and `endpointing` do not apply. It is the right pick when you want emotion, gender or end-of-turn detection out of the box, rather than a general replacement for `pulse`. Every final also carries `emotion` and `gender` objects with a label, a confidence and the full score distribution, plus `eot_finalized: true`, and diarization is on by default.

Set `eot_events=true` to also receive the live per-tick end-of-turn stream, which carries `p` and `fired`. Off by default, since the finals already tell you the turn closed.

## Real-time controls

- [End-of-utterance timeout](https://docs.smallest.ai/models/speech-to-text/features/end-of-utterance-timeout): how long Pulse waits after speech stops. Do not set it below 500, which closes the segment before the last word finishes decoding and splits a word across two transcripts.
- [Endpointing](https://docs.smallest.ai/models/speech-to-text/features/endpointing): finalize on trailing silence. On by default.
- [Finalize control](https://docs.smallest.ai/models/speech-to-text/features/finalize-control): `finalize_on_words` and `max_words`.
- [Keep-alive](https://docs.smallest.ai/models/speech-to-text/features/keep-alive): holding an idle connection open.
- [Inverse text normalization](https://docs.smallest.ai/models/speech-to-text/features/inverse-text-normalization): spoken form to written form.

## Key docs

- Quickstart: https://docs.smallest.ai/models/speech-to-text/realtime-web-socket/quickstart
- Response format: https://docs.smallest.ai/models/speech-to-text/realtime-web-socket/response-format
- Audio formats: https://docs.smallest.ai/models/speech-to-text/realtime-web-socket/audio-formats
- Best practices: https://docs.smallest.ai/models/speech-to-text/realtime-web-socket/best-practices
