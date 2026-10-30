# LiveKit Agents and Pipecat

Both have an official Smallest AI plugin. Install and configure it. Do not generate a WebSocket client for these two: a hand-written plugin shim has to track the framework's internal base classes, and those change between minor releases.

Verified on 2026-09-29 against `pipecat-ai` 1.12.0, `livekit-agents` 1.8.3, `livekit-plugins-smallestai` 1.8.3.

## Pipecat

Add `smallest` to the extras the project already declares. Installing `pipecat-ai[smallest]` on its own drops the extras the repo depends on, and the transport or LLM stops importing:

```bash
# if requirements.txt says pipecat-ai[openai,silero,daily]
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
        keywords="Rahul:3,Choudhary:3,Acme Bank:3",
        format=True,
    ),
)
```

Drop it into the pipeline where the previous STT service was. Nothing else about the STT wiring changes.

If adding the extra also upgrades `pipecat-ai` itself, the upgrade can move modules that have nothing to do with STT. Going to 1.12.0 moves the Daily transport from `pipecat.transports.services.daily` to `pipecat.transports.daily.transport`, so an existing `bot.py` stops importing until that line is updated. Pin the version the project already uses if you do not want the upgrade, and run the app's own import once after installing.

**What the plugin handles for you.** It sends `{"type":"finalize"}` when it receives `VADUserStoppedSpeakingFrame`, so Pipecat's VAD owns the turn boundary, and it sends keep-alives on an idle connection. It pushes `InterimTranscriptionFrame` for partials and `TranscriptionFrame` for finals.

**Settings it exposes:** `language`, `word_timestamps`, `full_transcript`, `sentence_timestamps`, `redact_pii`, `redact_pci`, `numerals`, `diarize`, `endpointing`, `keywords`, `format`.

**Not exposed:** `itn_normalize`, `eou_timeout_ms`, `vad_events`, `punctuate`, `capitalize`, `external_session_id`, `finalize_on_words`. If the integration needs one of these, say so rather than hand-rolling a client: the plugin is the supported path and the option can be added to it.

**VAD setting that matters.** Sending `finalize` too soon after the speaker stops truncates the last word. Pipecat's Silero analyzer defaults to `stop_secs=0.2`, which is on the edge. Set it to at least 0.3:

```python
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

vad_analyzer = SileroVADAnalyzer(params=VADParams(stop_secs=0.3))
```

## LiveKit Agents

```bash
pip install livekit-plugins-smallestai
```

```python
from livekit.plugins import smallestai

stt = smallestai.STT(
    language="en",
    eou_timeout_ms=800,
    keywords=[("Rahul", 3.0), ("Choudhary", 3.0), ("Acme Bank", 3.0)],
)
```

Pass it as the `stt` argument to `AgentSession`, replacing the previous provider. Nothing else changes.

**Set `eou_timeout_ms` explicitly.** The plugin defaults to `100`, and at that value the server finalizes before the last word is decoded, so a turn arrives split across two finals with the final word cut in half:

```
FINAL ' Please transfer 25,000 rupees to Rahul Chaudh'
FINAL ' ary'
```

Reproducible on every run at 100 and 300, clean at 500 and above. Use `800`, which matches the server default. A LiveKit agent that commits each final as a user turn would otherwise send the LLM two fragments instead of one sentence.

**Options it exposes:** `model`, `language`, `sample_rate`, `encoding`, `word_timestamps`, `diarize`, `eou_timeout_ms`, `endpointing`, `keywords`, `format`, `sentence_timestamps`, `redact_pii`, `redact_pci`, plus `api_key`, `http_session` and `base_url`.

The plugin's docstring says up to 10,000 keywords per session. The server caps it at 100 and rejects 101 with `keywords too large (max 100)`. The server is the limit that applies.

**Not exposed:** `itn_normalize`, `vad_events`, `numerals`, `punctuate`, `capitalize`, `external_session_id`, `finalize_on_words`, `full_transcript`.

**Region pinning** uses `base_url`, since the plugin builds the WebSocket URL from it:

```python
stt = smallestai.STT(language="ja", base_url="https://api.us.smallest.ai", eou_timeout_ms=800)
```

**Turn detection.** The plugin does not send `finalize`; it relies on server endpointing, and LiveKit's own turn detector sits on top of the finals it emits. That is fine for most agents. Keep `endpointing=True`.

## Both plugins

Transcripts come out of both plugins exactly as the server sends them, including a leading space and, after a mid-sentence split, a leading period. Trim those before the text reaches the LLM, in the handler where you receive the transcription frame or event.

## Other frameworks

No official plugin exists for the rest. Generate a client from `templates/python-websockets.py.tpl` or `templates/node-ws.ts.tpl` and wire it where the previous STT provider was. The rules in `turn-state.md` are what the two plugins above implement internally, so a hand-written client has to implement them explicitly.
