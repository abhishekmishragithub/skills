# Things that look right and are not

Every line here is something a client gets written with, and what actually happens when it runs. Check this list before generating code.

## Parameters that do not exist

| Written | What happens | Use instead |
| --- | --- | --- |
| `session_id=<call id>` | Silently ignored. Responses carry the server's own `session_id`, so the correlation you wanted is not there. | `external_session_id` |
| `include_utterances=true` | Silently ignored, no `utterances` in the response. | `sentence_timestamps` |
| `include_full_transcript=true` | Silently ignored. | `full_transcript` |
| `profanity_filter=true` | Silently ignored. Not part of the public streaming surface. | Filter in your own code. |
| `encoding=flac` | Rejected: `Invalid enum value. Expected 'linear16' \| 'linear32' \| 'alaw' \| 'mulaw' \| 'opus' \| 'ogg_opus'`. | One of the six. |
| `eou_timeout_ms=0` | Rejected: `Number must be greater than or equal to 100`, then the socket closes. | Omit it, or use 100 to 10000. |
| `endpointing_timeout`, `vad_threshold`, `vad_min_speech_ms` | Not part of the public surface. Do not set them. | Nothing; VAD sensitivity is server-tuned. |

Unknown query parameters are dropped without an error, so a typo in a parameter name looks like a silent no-op rather than a failure. Read back the URL the client builds before shipping it.

`emotion_detection` and `gender_detection` are accepted on the streaming connection, but no `emotion` or `gender` field comes back in streaming responses. Use the pre-recorded endpoint if you need them.

## Control messages

| Written | What happens |
| --- | --- |
| `{"type":"end"}` | Not a control message. It is treated as audio. No final arrives, the socket stays open until it times out, and the session slot stays held. Use `{"type":"close_stream"}`. |
| Closing the socket right after `close_stream` | The terminal transcript is lost. Wait for the message with `is_last: true` first. |
| `{"type":"finalize"}` sent the moment the speaker stops | Truncates the last word. Keep streaming audio for at least 300 ms first. |
| `{"type":"finalize"}` sent repeatedly, or once per partial | Each extra one returns an `is_final` with an empty transcript. Send it once per turn, on an external certainty event. |

## Authentication

| Written | What happens |
| --- | --- |
| `new WebSocket(url, ["Authorization", "Bearer " + key])` | HTTP 401. Subprotocols are not request headers. This is the single most common browser mistake. |
| `new WebSocket(url)` with the key set in a variable and never sent | HTTP 401. |
| `?api_key=<permanent API key>` from a browser | Works, and exposes your account key to anyone who opens developer tools. Use a short-lived token. |
| `?token=<key>` | HTTP 401. The parameter is `api_key`. |

## Response handling

| Written | What happens |
| --- | --- |
| Committing only on `is_final` where `is_last` is false | Drops the last utterance of the call. When the stream closes with speech still buffered, the transcript arrives on the `is_last` message. |
| Treating an empty `is_final` as a bug | Empty finals are normal after a redundant `finalize` or at stream shutdown. Ignore them instead of reprompting. |
| Treating the `from_finalize: true` final as a user turn | It is the acknowledgement of your `finalize`, one per request, and it is empty when the text had already been finalized. Commit the text, not the ack. |
| Sending partials to the LLM because they look stable | Partials are revised. Commit only on a final. |
| Concatenating consecutive finals with a space | For Indic scripts this can split a word across two finals and inject a space inside it. Join without a separator, or re-segment on your side. |

## Configuration that is technically valid and still wrong

| Written | What happens |
| --- | --- |
| `endpointing=false` to let the client own the turn | The server still finalizes on its own, about 2.5 s after speech ends, which is slower than leaving it on. There is no mode where the client is solely authoritative. Keep `endpointing=true` and send `finalize` when your detector fires. |
| Lowering `eou_timeout_ms` to cut turn latency | Latency does not change: 0.8 to 1.0 s from end of speech at every value. Below 500 the turn is finalized mid-word and arrives split across two finals. |
| `itn_normalize=true` on a yes/no or digit menu | Numbers spanning a pause are normalised in separate pieces and come out wrong. |
| `finalize_on_words=true` with `max_words` on open-ended turns | Splits a real user turn mid-sentence. |
| Boosting every spelling of a name at the same weight | The model can satisfy the boost with the spelling you did not want. Boost only the spelling you want emitted. |
| Client-side VAD gating that trims audio before the first phoneme | Short words are lost before they reach us. Keep 200 to 300 ms of pre-roll. |
| Using `wss://api.smallest.ai` for a region-gated language | Works from one network and fails from another, because the default host is latency-routed. Use the regional hostname. |
