# Connection reference

Everything the streaming WebSocket accepts. All of it is set as query parameters at connection time and cannot be changed while the socket is open. To change a profile mid-call, close and reopen.

## Endpoint and region

Path is `/waves/v1/stt/live`.

**Use `model=pulse`.** It is the recommended model for voice agents and the one this skill configures throughout: 38 languages, and the turn boundary is yours to tune through `endpointing` and `eou_timeout_ms`.

`model=pulse-2` is a different trade, not an upgrade. Reach for it only when the agent specifically needs per-utterance emotion and gender, or its built-in end-of-turn detection, and English-only is acceptable. It exposes no endpointing knobs, and its finals carry `eot_finalized: true` alongside `emotion` and `gender` objects. If you do use it, check segmentation against your own audio first: on the clip used throughout this skill it split the final word across two finals on 5 of 5 runs, where `pulse` at its defaults returned one clean final.

`pulse-pro` is pre-recorded only and is rejected with HTTP 400 before the upgrade.

| Host | Use for |
| --- | --- |
| `wss://api.smallest.ai/waves/v1/stt/live` | Default. Routed to the nearest region, so which region you land on is not fixed. Fine for languages enabled in every region. |
| `wss://api.us.smallest.ai/waves/v1/stt/live` | Required for `zh`, `yue`, `ja`, `ko`, `multi-asian`. |
| `wss://api.india.smallest.ai/waves/v1/stt/live` | Required for `ta`, `te`, `kn`, `ml`, `multi-south-indic`. Also the way to pin India for data residency. |

Do not use the default host for a region-gated language. Because it is latency-routed, the same request can succeed from one network and fail from another. A language that is not enabled in the region you land on fails like this, after the WebSocket has already opened:

```json
{"type":"error","error_code":"LANGUAGE_NOT_ENABLED_IN_REGION","message":"Language 'ja' has not been enabled in this region. Please contact support to request access.","language":"ja","region":"ap-south-1"}
```

## Authentication

| Client | Form |
| --- | --- |
| Server-side | `Authorization: Bearer <SMALLEST_API_KEY>` |
| Browser or mobile | `Authorization: Bearer <short-lived token>` |
| Browser using `new WebSocket()` | `?api_key=<short-lived token>` |

The `api_key` query parameter also accepts a permanent API key. Do not use it that way from a browser: the key would be visible in the page, in the URL, and in every log along the path.

### Short-lived tokens

The customer's backend mints a token from the API key and hands it to the client.

```bash
curl -X POST "https://api.smallest.ai/waves/v1/auth/token" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ttl_seconds": 300}'
```

```json
{"access_token":"wat_...","token_type":"Bearer","expires_in":300,"expires_at":"2026-09-29T13:01:14.533Z"}
```

- `ttl_seconds` is 30 to 900, and defaults to 300.
- A token works any number of times until it expires. After that the connection is refused with HTTP 401 before the upgrade, so the client must mint a new one and reconnect.
- A token cannot mint another token; that returns 403.
- A token is valid only in the region that minted it. Mint through the same hostname the client will connect to.
- Usage is billed to the API key that minted the token.

Full reference: [Token-based authentication](https://docs.smallest.ai/models/api-reference/token-based-authentication).

## Audio

| Parameter | Default | Notes |
| --- | --- | --- |
| `encoding` | `linear16` | `linear16`, `linear32`, `alaw`, `mulaw`, `opus`, `ogg_opus`. Use `linear16` for agent frameworks, `mulaw` or `alaw` for telephony. |
| `sample_rate` | `16000` | `8000`, `16000`, `22050`, `24000`, `44100`, `48000`. Must match the audio actually sent. A mismatch produces a garbled transcript with no error. |

Send binary frames of 20 to 40 ms. Do not base64-encode.

## Language and formatting

| Parameter | Default | Notes |
| --- | --- | --- |
| `language` | `multi` | Always set it explicitly. Leaving it out selects multi-language detection, which can tag short English audio as another language. |
| `format` | `true` | Master switch. `false` also forces off punctuation, capitalisation and ITN. |
| `punctuate` | `true` | |
| `capitalize` | `true` | To lowercase the output, set this to `false`, not `format=false`. |
| `itn_normalize` | `false` | Spoken form to written form, for example "twenty five thousand" to "25,000". Turn it off for short-reply turns. |
| `numerals` | `auto` | `auto`, `true` (words to digits), `false` (digits to words). Tri-state, not a boolean. Note it acts independently of `itn_normalize`: with ITN off and `numerals` at its default, "twenty five thousand" still comes back as `25,000`. Setting `numerals=false` mangles compound numbers (`twenty-five,zero`), so it is not a reliable way to get spoken form. |

## Turn boundary

| Parameter | Default | Notes |
| --- | --- | --- |
| `endpointing` | `true` | Finalizes on trailing silence. Leave it on for voice agents. |
| `eou_timeout_ms` | server default | Integer 100 to 10000. **`0` is rejected.** Not a latency control: end of speech to final stays at 0.8 to 1.0 s at every value. Below 500 the server finalizes before the last word is decoded and one word arrives split across two finals. Leave it unset. |
| `finalize_on_words` | `true` | Set `false` for voice agents so a long user turn is not split by word count. |
| `max_words` | unset | Forces a final every N words. Do not set it for voice agents. |

With `endpointing=true`, a final arrives roughly 0.8 to 1.0 s after the speaker stops, whatever `eou_timeout_ms` says. Measured across values 100 to 1500 on clips from 1 to 33 seconds. The knob that would move this is server-tuned and not client-configurable. If you need to commit a turn sooner than that, send `{"type":"finalize"}` from your own end-of-turn detector.

What `eou_timeout_ms` does change is where the transcript is cut. Below 500 the server finalizes before the last word is decoded:

```
eou=100   'Please transfer 25,000 rupees to Rahul Chaudh' || ' ary'
eou=300   'Please transfer 25,000 rupees to Rahul Chaud'  || ' hary'
eou=500   'Please transfer 25,000 rupees to Rahul Chaudhary.'
```

An 8 s sentence returned 5 finals at 100, 4 at 300, and 3 from 500 upwards. So there is no latency to gain by lowering it, and a real cost.

## Voice activity events

| Parameter | Default | Notes |
| --- | --- | --- |
| `vad_events` | `false` | Turn it on. Emits `speech_started` and `speech_ended` messages, which is how barge-in is triggered without waiting for a transcript. |

`speech_started` and `speech_ended` carry a `timestamp` in seconds measured from the first audio frame on the connection, not a wall clock.

## Biasing

| Parameter | Default | Notes |
| --- | --- | --- |
| `keywords` | unset | Comma-separated `phrase:intensifier`, for example `Blackwell:2,Jensen Huang:2`. Phrases may contain spaces. Matching is case-sensitive. Maximum 100 entries; 101 is rejected with `keywords too large (max 100)`. |

Weighting ladder:

- `1` for a term you are adding speculatively, because it appears in the domain.
- `3` for a term you already know the model gets wrong. Phrases the customer volunteers when asked "what does it mis-transcribe" belong here, which is why the profiles start domain phrases at `:3`.
- `4` or `5` for a term still wrong at `3`.
- Above `5` the model starts inserting the word when it was not spoken.

The weight a given name needs varies with the speaker and the audio quality, so treat the ladder as a starting point and re-measure on the customer's own recordings.

When you supply spelling variants of a name, boost only the spelling you want in the transcript. Boosting every variant at the same weight lets the model satisfy the boost with the spelling you did not want.

## Post-processing

| Parameter | Default | Notes |
| --- | --- | --- |
| `word_timestamps` | `false` | Per-word `start`, `end`, `confidence`. |
| `sentence_timestamps` | `false` | Sentence-level `utterances`. |
| `full_transcript` | `false` | Each message also carries the transcript accumulated since the connection opened. |
| `diarize` | `false` | Speaker labels on words, plus `diarization_segments`. Up to 8 speakers. |
| `redact_pii` | `false` | Replaces personal data with placeholders such as `[FIRSTNAME_1]`. |
| `redact_pci` | `false` | Replaces payment data with placeholders such as `[CREDITCARDCVV_1]`. |

Redaction rewrites the transcript in place, and it will also mask numbers an agent needs, such as an order ID. For a live agent, run without redaction on the path the LLM reads and redact the copy you store.

## Session and connection

| Parameter | Default | Notes |
| --- | --- | --- |
| `external_session_id` | unset | Your own call ID, for correlating usage records. Letters, digits, hyphen, underscore and dot; up to 128 characters. It is not echoed back: responses carry only the server's own `session_id`. |
| `timeout` | see below | Connection inactivity timeout in seconds. |

An idle connection is closed with `{"status":"error","message":"Connection timed out after N seconds of inactivity"}`. Any inbound frame resets the timer, including a keep-alive. On a connection with no `timeout` set and no traffic at all, the socket was dropped after about 4 minutes in testing, so send a keep-alive at least every 2 minutes during silence rather than relying on the configured value.

## Control messages

Sent as JSON text frames.

| Message | Effect |
| --- | --- |
| `{"type":"finalize"}` | Forces an immediate final for the audio buffered so far. The socket stays open. |
| `{"type":"close_stream"}` | Flushes, emits the terminal final with `is_last: true`, then closes. |
| `{"type":"ping"}` | Keep-alive. The server replies `{"type":"pong"}`. `keepalive`, `keep_alive` and `keep-alive` behave the same. |

There is no `{"type":"end"}`. A JSON frame with an unrecognised type is treated as audio, so the session stays open until it times out.

Before sending `finalize`, keep streaming audio for at least 300 ms after the speaker stops. Sending it earlier truncates the last word. See `failure-modes.md`.

## Responses

A transcription message carries `transcript` (and the identical `transcription`), `is_final`, `is_last`, `session_id`, and on finals `language`.

- `from_finalize: true` marks the response to a client `{"type":"finalize"}`. Exactly one arrives per request, and it carries an empty transcript when the text had already been finalized.
- Commit a turn on any `is_final` with a non-empty transcript, **including `is_last: true`**. When the stream is closed while speech is still buffered, the last utterance arrives on that message.
- An `is_final` with an empty transcript is normal. Ignore it.
- Transcripts may start with a space, and after a mid-sentence split with a period. Trim both.

### Server-initiated shutdown

During a deploy the server asks open connections to leave before it closes them:

```json
{"status":"info","type":"server_shutdown","message":"Server is shutting down. Please close your connection.","reconnect":true,"deadline_ms":60000}
```

It arrives about a minute before the connection is closed with WebSocket code `1012`. Handle it: finish the turn in flight, send `close_stream`, open a new connection. A client that ignores it loses whatever was buffered when the 1012 lands. Note it carries `status: "info"`, not `type: "error"`, so a handler that branches only on errors will miss it.
