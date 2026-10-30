# Failure modes

The five things that actually go wrong, with the measurement behind each fix.

## 1. The last word is cut off

**Looks like:** `"...to Rahul Chaudh"` instead of `"...to Rahul Chaudhary"`, or the final word of a turn missing entirely.

**Cause A: `finalize` sent too early.** Sending `{"type":"finalize"}` the instant your VAD reports silence cuts the word that is still being decoded. Streaming trailing audio before the finalize fixes it:

| Trailing audio streamed before `finalize` | Result |
| --- | --- |
| 0 ms | truncated, 3 of 3 runs |
| 150 ms | truncated, 2 of 2 |
| 200 ms | complete, 3 of 3 |
| 300 ms and above | complete, 7 of 7 |

Keep sending audio for at least 300 ms after your VAD fires, then send `finalize` once.

**Cause B: `eou_timeout_ms` set too low.** At 100 or 300 the server finalizes mid-word and the rest arrives as a separate final:

```
eou=100   'Please transfer 25,000 rupees to Rahul Chaudh' || ' ary'
eou=300   'Please transfer 25,000 rupees to Rahul Chaud'  || ' hary'
eou=500   'Please transfer 25,000 rupees to Rahul Chaudhary.'
```

Do not set `eou_timeout_ms` below 500. Leaving it out is the safest choice. Lowering it does not commit turns faster: time from end of speech to final stays at roughly 0.8 to 1.0 s at every value.

**Cause C: the socket was closed too early.** After `{"type":"close_stream"}`, wait for the message with `is_last: true`. When speech is still buffered at close, the last utterance arrives on that message and nowhere else.

## 2. One user turn arrives as several

**Looks like:** the agent replies to half a sentence, or the LLM receives two messages for one thing the caller said.

- `finalize_on_words=true` with `max_words` splits by word count. Set `finalize_on_words=false` and omit `max_words`.
- A low `eou_timeout_ms` splits on natural pauses. An 8 s sentence came back as 5 finals at `eou=100`, 4 at 300, and 3 from 500 upwards.
- The client committed each final without checking whether the caller had finished. Server endpointing finalizes on silence, so a long thinking pause is a turn boundary from our side. If your framework has a turn detector, let it decide when to call the LLM and use our finals as input to it.

## 3. Short replies are wrong or missing

**Looks like:** "four" comes back as "for" or "F", "no" transcribed as nothing, one-word answers lost.

The usual cause is upstream. Client-side VAD gating that starts sending on speech onset removes the first phoneme before the audio reaches us. It bites hardest on telephony audio. Measured on real recordings of single spoken digits:

| Condition | Result |
| --- | --- |
| 8 kHz, clip starts at speech onset | 3 of 9 returned no transcript at all |
| 8 kHz, 500 ms of leading audio | all but one recovered |
| 16 kHz, either way | no measurable difference on clean audio |

An agent that handles short replies correctly on headset audio can still lose them once it is on a phone line.

Fixes, in order of impact:

1. Send 200 to 300 ms of audio from before speech onset. If your VAD gates the stream, buffer and prepend.
2. Test with noise suppression and AGC off first. Aggressive onset processing clips word starts.
3. Put the expected reply grammar in `keywords` (`yes:3,no:3,one:2,two:2,...`).
4. Set `itn_normalize=false` on short-reply connections.

## 4. Names, IDs and domain terms come out wrong

**Looks like:** "Choudhary" as "Chaudhary", product names as common words, alphanumeric IDs mangled.

- Put the terms in `keywords`, using the weighting ladder in `config-knobs.md`: `1` for a speculative addition, `3` for a term you already know is wrong, `4` or `5` if it is still wrong at `3`, and never above `5`.
- The weight a term needs depends on the speaker and the audio. The same name needed `:3` on one recording and `:5` on another. Measure on the customer's own audio.
- Boost only the spelling you want emitted. Listing `Choudhary:3,Chaudhary:3,Choudhari:3` together lets the model satisfy the boost with the spelling you did not want, which is the opposite of the intent.
- Keywords are case-sensitive and stream-scoped. Maximum 100 per connection.

## 5. Numbers come out wrong

**Looks like:** an order ID read back as the wrong digits, currency formatted oddly, "four hours" rendered as "4 h".

- ITN normalizes each final independently. A number spoken across a pause is normalized in pieces: "one two three, nine eight seven" finalized separately came back as `123.` and `987.` and then a merged `123987` later in the call.
- On short-reply or digit-collection turns, set `itn_normalize=false` and convert on your side, where you know what the field expects.
- `itn_normalize=false` on its own does not give you spoken-form numbers. `numerals` defaults to `auto` and still converts: with ITN off, "twenty five thousand rupees" came back as `25,000 rupees`.
- `numerals=false` is not a safe way to force words either. On a digit sequence it works ("one, two, three"), but on a compound number it mangles: "twenty five thousand" came back as `twenty-five,zero`, reproducible on every run. For digit collection, take the digits as returned and parse them rather than trying to get words back.
- `numerals` is tri-state (`auto`, `true`, `false`), not a boolean.
- ITN substitutes currency symbols, not just digits: "twenty five thousand rupees" comes back as `₹25000`, with the word "rupees" gone. Anything downstream that parses amounts by looking for the currency word will miss it.
- Unit and currency normalization is not exact. "Four hours of steady work" came back as "4 h of steady work".

## Diagnostic dump

For any of the above, capture these four things before reporting it:

1. The connection URL with every query parameter.
2. The full sequence of JSON messages with monotonic timestamps.
3. The `session_id` from the response.
4. The exact PCM sent for that turn, including any pre-roll, as a WAV.

The [customer harness](https://github.com/smallest-inc/cookbook/tree/main/speech-to-text/customer-harness) in the cookbook reproduces all five failure modes above against your own recordings, and dumps exactly this.
