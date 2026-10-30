# LiveKit Agents and Pipecat

Both have an official Smallest AI plugin. Install and configure it. Do not generate a WebSocket client for these two: a hand-written plugin shim has to track the framework's internal base classes, and those change between minor releases.

Verified on 2026-09-29 against `pipecat-ai` 1.12.0, `livekit-agents` 1.8.3, `livekit-plugins-smallestai` 1.8.3.

## Pipecat

Add `smallest` to the extras the project already declares, and drop the extra for the provider you are replacing. Installing `pipecat-ai[smallest]` on its own removes the extras the repo depends on, and the transport or LLM stops importing:

```bash
# requirements.txt said pipecat-ai[deepgram,openai,silero,daily]
pip install "pipecat-ai[smallest,openai,silero,daily]"
```

```python
import os
from pipecat.services.smallest.stt import SmallestSTTService
from pipecat.transcriptions.language import Language

stt = SmallestSTTService(
    api_key=os.environ["SMALLEST_API_KEY"],
    sample_rate=16000,
    settings=SmallestSTTService.Settings(
        language=Language.EN,
        endpointing=True,
        itn_normalize=True,          # false for short-reply and digit turns
        keywords="Rahul:3,Choudhary:3,Acme Bank:3",
        format=True,
    ),
)
```

Drop it into the pipeline where the previous STT service was. If adding the extra also upgrades `pipecat-ai` itself, run the app's own import once afterwards: 1.12.0 moved the Daily transport to `pipecat.transports.daily.transport`, which has nothing to do with STT but stops an older `bot.py` importing.

**What the plugin handles.** It sends `{"type":"finalize"}` on `VADUserStoppedSpeakingFrame`, so Pipecat's VAD owns the turn boundary, and it keeps the connection alive when idle. It pushes `InterimTranscriptionFrame` for partials and `TranscriptionFrame` for finals, and it strips the transcript, so the leading space is already gone by the time you see it. A leading period after a mid-sentence split is not stripped.

**Settings it exposes** (1.15.0): `language`, `word_timestamps`, `full_transcript`, `sentence_timestamps`, `redact_pii`, `redact_pci`, `numerals`, `diarize`, `endpointing`, `keywords`, `format`, `itn_normalize`, `no_format_delay`, `emotion_detection`, `gender_detection`, plus `model` on the constructor.

**Not exposed:** `eou_timeout_ms`, `vad_events`, `punctuate`, `capitalize`, `external_session_id`, `finalize_on_words`. The last one matters for open-ended turns, because it leaves the server default of `true` in place and a long turn can be split by word count.

**VAD setting that matters.** Sending `finalize` too soon after the speaker stops truncates the last word. Pipecat's Silero analyzer defaults to `stop_secs=0.2`, which is on the edge. Set it to at least 0.3:

```python
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

vad_analyzer = SileroVADAnalyzer(params=VADParams(stop_secs=0.3))
```

**Two gaps to plan around.** Neither is something the plugin lets you configure.

- It never sends `{"type":"close_stream"}`. It closes the socket directly, so whatever was still buffered when the call ends is dropped. If the last thing a caller says matters, do not rely on the tail of the session.
- It drops server error messages. Its response handler returns early on any message with no transcript, and a `{"type":"error"}` frame has none, so a rejected parameter or a region-gated language arrives as silence rather than an error. If a Pipecat integration produces no transcripts at all, check the connection parameters by hand before looking at the audio.

## LiveKit Agents

```bash
pip install livekit-plugins-smallestai
```

```python
from livekit.plugins import smallestai

stt = smallestai.STT(
    language="en",
    endpointing_timeout_ms=None,          # see the warning below
    itn_normalize=False,                  # for short-reply and digit turns
    finalize_on_words=False,
    vad_events=True,
    keywords=[("Rahul", 3.0), ("Choudhary", 3.0), ("Acme Bank", 3.0)],
)
```

Pass it as the `stt` argument to `AgentSession`, replacing the previous provider.

**Set `endpointing_timeout_ms` explicitly.** The plugin defaults it to `300` and sends it on every connection. At that value the server closes the segment before the last word finishes decoding, and a turn arrives split:

```
' Please transfer 25,000 rupees to Rahul Chaud'
' hary.'
```

Reproducible every run at `300`, clean at `600` and above and when the parameter is omitted. Pass `None` to fall back to the server default, or a value of `600` or more. This is the same failure the `eou_timeout_ms` default used to cause in 1.8.3; that default was fixed, this one has not been.

`eou_timeout_ms` now defaults to `None`, which means the server default of 800, so there is no longer any need to pass it.

**Options it exposes** (1.8.10): `model`, `language`, `sample_rate`, `encoding`, `word_timestamps`, `diarize`, `eou_timeout_ms`, `endpointing`, `endpointing_timeout_ms`, `itn_normalize`, `numerals`, `finalize_on_words`, `max_words`, `finalize_on_flush`, `keywords`, `format`, `sentence_timestamps`, `redact_pii`, `redact_pci`, `keepalive_interval`, `stream_path`, plus `api_key`, `http_session` and `base_url`.

**Not exposed:** `punctuate`, `capitalize`, `external_session_id`, `full_transcript`. `punctuate` and `capitalize` default to `true` on the server, which is what the profiles want anyway.

**Region pinning** goes through `base_url`, which must keep the `/waves/v1` segment because the plugin appends only `stream_path` to it:

```python
stt = smallestai.STT(language="ja", base_url="https://api.us.smallest.ai/waves/v1")
```

Dropping `/waves/v1` yields `wss://api.us.smallest.ai/stt/live` and the connection fails.

**Trimming the leading space** has to happen somewhere that changes what reaches the LLM. `AgentSession`'s `user_input_transcribed` event is observational, so trimming there is a no-op. Override `stt_node` on your `Agent` instead and clean each event as it passes through.

**Turn detection.** The plugin does not send `finalize`; it relies on server endpointing, and LiveKit's own turn detector sits on top of the finals it emits. Keep `endpointing=True`.

**Checking it offline.** The plugin needs a job context, so calling `.stream()` from a script raises `RuntimeError: Attempted to use an http session outside of a job context`. Wrap the check:

```python
from livekit.agents.utils import http_context

async with http_context.open():
    stream = stt.stream()
    ...
```

Reading back `stream._ws_url()` is the quickest way to confirm the plugin is sending the parameters you intended, which `verify.py` cannot tell you.

## Both plugins

A leading period can survive a mid-sentence split on either plugin, so trim it somewhere that changes what reaches the LLM. Pipecat already strips the leading space; the LiveKit plugin does not.

Neither plugin implements all of the turn-state rules on its own. The Pipecat one does not send `close_stream` and swallows server error frames; the LiveKit one does not send `finalize` at all. Read the per-plugin notes above before promising a customer a behaviour from `turn-state.md`.

## Other frameworks

No official plugin exists for the rest. Generate a client from `templates/python-websockets.py.tpl` or `templates/node-ws.ts.tpl` and wire it where the previous STT provider was. `turn-state.md` describes what a correct client does. A hand-written client has to implement all of it; the two plugins above implement most of it, with the gaps listed in their sections.
