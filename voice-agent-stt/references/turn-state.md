# Turn state machine

Most "the STT is broken" reports are a client turn state machine, not the transcription. This is the shape that works.

```
IDLE ──speech_started──▶ USER_SPEAKING ──speech_ended──▶ WAITING_FINAL
  ▲                            │                              │
  │                     stop TTS (barge-in)                    │
  └────────── commit ◀── is_final with text ◀──────────────────┘
```

## Rules

1. **Commit on a final, never on a partial.** Partials are revised until the final arrives.
2. **Commit on any `is_final` carrying text, including `is_last: true`.** When the connection is closed while speech is still buffered, the last utterance arrives on the `is_last` message. A client that skips it drops the caller's last sentence.
3. **Ignore an `is_final` with an empty transcript.** It happens after a redundant `finalize`, and at stream shutdown when nothing was pending. It is not an error and must not trigger a reprompt.
4. **`speech_started` stops TTS, and nothing else.** Barge-in is a playback decision. The turn is still committed on the final.
5. **`{"type":"finalize"}` is edge-triggered.** Send it once per turn, on an external certainty event: your VAD or end-of-turn model fired, the caller released push-to-talk, the dialog decided the turn is done. Never on a partial that "looks stable".
6. **Keep streaming audio for at least 300 ms after the speaker stops before sending `finalize`.** Sending it immediately truncates the last word.
7. **Server endpointing is a floor, not something `finalize` overrides.** With `endpointing=true`, which these profiles keep on, the server's own final frequently lands before your `finalize` does on short and medium turns. When that happens the commit carries `from_finalize: false` and your finalize comes back as an empty acknowledgement. Your detector only buys latency when it is confident earlier than the endpointing window, so treat `finalize` as "commit sooner when I am sure", not as "I own the boundary".
8. **Match the final to your `finalize` using `from_finalize`.** The response to a client `finalize` carries `from_finalize: true`. There is exactly one per finalize, and it can be empty when everything had already been finalized, so treat an empty one as an acknowledgement rather than a turn.

## Timing to expect

| Event | Typical |
| --- | --- |
| WebSocket connect | 0.2 to 0.9 s depending on region distance |
| `speech_started` after speech actually starts | under 100 ms |
| Final after the speaker stops, `endpointing=true` | 0.8 to 1.0 s |
| Final after the speaker stops, `endpointing=false` | about 2.5 s |
| Final after a client `finalize` | under 500 ms |

The end-of-speech to final figure does not move with `eou_timeout_ms`. If you need a turn committed sooner, send `finalize` from your own detector.

## Telemetry worth logging

Log these per turn. They are the first thing support will ask for.

| Metric | How to compute | Healthy |
| --- | --- | --- |
| `time_to_first_partial_ms` | first partial timestamp minus the `speech_started` timestamp | under 500 ms |
| `speech_ended_to_final_ms` | final timestamp minus the `speech_ended` timestamp | 0.8 to 1.0 s with endpointing on |
| `finalize_to_final_ms` | the `from_finalize: true` final minus the time you sent `finalize` | under 500 ms |
| `empty_final_count` | finals with no text | roughly one per turn where you sent a redundant `finalize`, otherwise zero |
| `turns_with_no_partial` | turns where a final arrived with no partial before it | normal for one-word replies |

Measure from `speech_started`, not from when the session opened. A metric measured from session start reports the age of the connection, not the latency of the turn.

## Diagnostic dump

For a wrong or missing transcript, capture: the connection URL with all parameters, the full sequence of JSON messages with monotonic timestamps, the `session_id` from the response, and the exact PCM sent for that turn including any pre-roll. Those four make the difference between a fixable report and a guess.
