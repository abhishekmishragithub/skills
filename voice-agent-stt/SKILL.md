---
name: voice-agent-stt
description: Wire Smallest AI streaming speech-to-text (Pulse) into a voice agent. Use when
  adding or switching STT inside a LiveKit Agents, Pipecat, custom Python, Node or browser
  voice agent, when turns are committing wrong (last word cut off, one turn arriving as
  several, short replies missed), or when choosing how a browser client should authenticate.
  For plain transcription of files or a bare WebSocket, use the speech-to-text skill instead.
license: MIT
compatibility: Requires internet access and a Smallest AI API key (SMALLEST_API_KEY). Python 3.10+ with the websockets package for the verification script.
---

# Smallest AI STT for voice agents

Wires Smallest AI's streaming STT into an existing voice agent in one pass. STT only: it does not touch the LLM, TTS, or dialog code.

> **Setup:** requires `SMALLEST_API_KEY`. See the `setup-api-key` skill.
>
> **Only transcribing audio?** The `speech-to-text` skill covers the pre-recorded and plain streaming surfaces. This skill is for putting STT inside an agent that takes turns.

Tested against `pipecat-ai` 1.12.0, `livekit-agents` 1.8.3 and `livekit-plugins-smallestai` 1.8.3 on 2026-09-29. If the installed version is newer, check the plugin's own parameter list before assuming the options below still match.

## Step 1. Detect the stack

Run `scripts/detect-stack.sh` from the repo root. It prints one of `livekit | pipecat | node-ws | python-websockets | browser | unknown`, and on a second line the STT provider already wired, as `stt=<name>` (`deepgram`, `assemblyai`, `speechmatics`, `gladia`, `rev_ai`, `cartesia`, `whisper`, `google`, `azure`, or `none`). That is what you are replacing.

## Step 2. Ask five questions

Read the answers off the existing integration first: the current STT call usually settles the audio format and the language, and the framework settles who owns the turn. Ask with `AskUserQuestion` only about what is left. Every answer changes generated code, so do not guess at the rest.

1. **Where does the audio come from?** A server the user controls (backend, telephony bridge, agent worker), or a browser or mobile client. This decides authentication: a browser must never hold the permanent API key.
2. **Audio format.** 16 kHz PCM (default for agent frameworks), 8 kHz telephony (`mulaw` or `alaw`), or Opus. This decides `encoding` and `sample_rate`, and whether the pre-roll warning in `references/failure-modes.md` applies.
3. **Who decides the turn is over?** Our server endpointing (default, simplest), or the caller's own VAD or end-of-turn model, which then sends `{"type":"finalize"}`. There is no third option: server endpointing cannot be switched off in a way that leaves the client authoritative. See `references/turn-state.md`.
4. **Language**, and whether callers code-switch. This decides `language` and, for region-gated languages, the hostname. See the region table in `references/config-knobs.md`.
5. **Domain phrases to bias.** Names, products, expected reply words. Becomes `keywords`. Read the weighting rules in `references/config-knobs.md` before choosing values, and the alias trap in `references/common-mistakes.md`.

## Step 3. Wire the integration

Read `references/common-mistakes.md` first. It lists the parameters and control messages that do not exist, which is the most common way this integration is written wrong.

**LiveKit Agents and Pipecat have official plugins. Use them.** Do not generate a WebSocket client for these two. `references/frameworks.md` has the install command, the constructor with every option the plugin exposes, the options it does not expose, and the VAD settings that matter.

- `livekit` → `pip install livekit-plugins-smallestai`, swap the STT service in the agent session.
- `pipecat` → `pip install "pipecat-ai[smallest]"`, swap the STT service in the pipeline.
- `python-websockets` → `templates/python-websockets.py.tpl`
- `node-ws` → `templates/node-ws.ts.tpl`
- `browser` → `templates/browser-token.ts.tpl` plus one of `templates/token-mint.py.tpl` or `templates/token-mint.ts.tpl` for the customer's backend.
- `unknown` → ask which language the audio loop is written in, then use the Python or Node template.

Every generated client must:

- Send binary PCM in the declared `encoding` at the declared `sample_rate`. No base64. Chunks of 20 to 40 ms.
- Commit a user turn on any `is_final` message carrying a non-empty transcript, **including one with `is_last: true`**. A short final utterance often arrives only on the `is_last` message.
- Ignore `is_final` messages with an empty transcript. They are normal.
- Trim the leading space and any leading period from a transcript before sending it to the LLM. This applies to the official plugins too: they pass the transcript through unchanged.
- Handle `{"type":"error"}` messages, which arrive after a successful WebSocket upgrade. A bad parameter or a region-gated language fails this way, not with an HTTP error.
- Send `{"type":"ping"}` during silence and `{"type":"close_stream"}` at the end, then wait for `is_last` before closing the socket.
- If the caller owns the turn boundary, keep streaming audio for at least 300 ms after their detector fires, then send `{"type":"finalize"}` once. Finalizing immediately truncates the last word.

## Step 4. Authentication

Three accepted forms. Pick from the answer to question 1.

| Client | Form |
| --- | --- |
| Server-side | `Authorization: Bearer <SMALLEST_API_KEY>` |
| Mobile or native, which can set headers | `Authorization: Bearer <short-lived token>` |
| Browser, using `new WebSocket()` | `?api_key=<short-lived token>` in the URL |

A browser cannot set request headers on a WebSocket, so the query parameter is the only form available to it. Passing the credential as a subprotocol does not work; it returns 401. For a browser, the customer's backend mints a short-lived token with `POST /waves/v1/auth/token` and the page fetches one before connecting. Full flow in `references/config-knobs.md`.

## Step 5. Verify

Run `scripts/verify.py` with the chosen configuration. It streams the bundled sample at `assets/verify-sample.wav` and fails unless a final transcript comes back containing the expected words. It prints the server's error message when a parameter is rejected.

Verify the configuration you are actually shipping, including how it authenticates.

Pass the flags you are actually shipping. The script's defaults are the server's defaults, not a profile, so anything you set on the connection you should set here too.

```
# server-side client, open-ended profile
python scripts/verify.py --language en --itn-normalize true --keywords "Acme Bank:3"

# browser client: mint a short-lived token and connect with no request headers,
# which is the only form a browser can use
python scripts/verify.py --language en --itn-normalize true --keywords "Acme Bank:3" --token --query-auth

# telephony: the bundled sample is converted, so the mulaw path is really tested
python scripts/verify.py --language en --encoding mulaw --sample-rate 8000

# a region-gated language
python scripts/verify.py --host api.us.smallest.ai --language ja --expect ""
```

A pass means auth, region, the parameters you passed, and the audio path all work together. Do not report the integration as done before the command matching your auth mode passes.

On LiveKit and Pipecat the plugin decides the final parameter set, and it is not the same list this script sends. A pass proves the account, region and audio path; it does not prove the plugin is sending the profile you intended. Confirm that by running the agent and checking a transcript.

## Step 6. Write `SMALLEST_STT_CONFIG.md`

Emit this file in the repo root. It is the record of what was built and the first thing support will ask for. Include:

- Endpoint host, and why that host (region gating or default routing).
- Every query parameter with a one-line reason.
- Authentication mode, and for tokens, where the mint endpoint lives in the customer's backend.
- Audio format, sample rate, chunk size.
- Who owns the turn boundary, and if the client does, where `finalize` is sent from.
- The keyword list with weights.
- The verify command that passed and the transcript it returned.

## Step 7. Close out

Print a short summary in the same shape as the config file: stack, endpoint, auth mode, turn owner, keywords, verify result. Then point at `references/failure-modes.md` and the [customer harness](https://github.com/smallest-inc/cookbook/tree/main/speech-to-text/customer-harness) in the cookbook, for tuning against the customer's own recordings.

## Config profiles

Starting points. `references/config-knobs.md` has the full parameter list.

### Open-ended user turns (support, sales)

```
model=pulse
language=en
sample_rate=16000
encoding=linear16
format=true&punctuate=true&capitalize=true
itn_normalize=true
endpointing=true
finalize_on_words=false
vad_events=true
keywords=<domain phrases>:3
external_session_id=<your call id>
```

### Short replies (yes/no, digits, menus)

Same, with `itn_normalize=false` and the expected reply grammar in `keywords`. ITN on short segments produces wrong numbers.

### Mixed traffic on one call

Most telephony agents carry both: account numbers and open questions on the same connection. Configuration cannot change while the socket is open, so pick one profile for the call rather than reconnecting per turn. Start from the short-reply profile, because a wrong digit is a correctness bug while an un-normalized amount on an open-ended turn is cosmetic, and handle number parsing on your side. Read the `numerals` note in `references/failure-modes.md` before assuming `itn_normalize=false` gives you spoken words: it does not.

`eou_timeout_ms` is left out of both profiles on purpose. It is not a latency control: time from end of speech to final is 0.8 to 1.0 s whatever it is set to. Below 500 it makes the server finalize before the last word is decoded, so a turn arrives split across two finals. Leave it unset. See `references/config-knobs.md`.

**One exception.** The LiveKit plugin does not leave it unset: it defaults to `100` and always sends it, which is the value that splits words. On LiveKit, pass `eou_timeout_ms=800` explicitly.

### These profiles are a server-side parameter list

They describe what the connection should carry. A generated client can set all of it. The official plugins cannot: each exposes a subset, and `itn_normalize`, `vad_events` and `external_session_id` are exposed by neither. Before promising a customer a profile line on LiveKit or Pipecat, check the exposed lists in `references/frameworks.md`, set what you can, and tell them plainly which lines are not reachable through the plugin and what the effect is. Do not hand-roll a client to get at a missing option: the option can be added to the plugin, and a shim cannot.

## Non-goals

- Does not touch the LLM, TTS, or dialog code.
- Does not create commits.
- `scripts/verify.py` needs network access, so it does not run in an offline CI job.
