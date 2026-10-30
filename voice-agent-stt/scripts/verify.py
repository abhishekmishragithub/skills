"""End-to-end check for a Smallest AI streaming STT configuration.

Streams the bundled sample through the WebSocket with the configuration you
pass, and fails unless a final transcript comes back containing the expected
words. A pass means authentication, region, parameters and the audio path all
work together.

  python verify.py                                  # defaults
  python verify.py --language en --keywords "Acme:3"
  python verify.py --host api.us.smallest.ai --language ja --expect ""
  python verify.py --token                          # mint and use a short-lived token

Requires: websockets. `--token` also requires requests.
Reads SMALLEST_API_KEY from the environment.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import wave
from pathlib import Path
from urllib.parse import urlencode

try:
    import websockets
except ImportError:
    sys.exit("verify: websockets is not installed. pip install websockets")

SAMPLE = Path(__file__).resolve().parent.parent / "assets" / "verify-sample.wav"

# What the bundled sample says. Stable across ITN and formatting settings.
DEFAULT_EXPECT = "quick,brown,fox,lazy,dog"

TELEPHONY_SAMPLES = {
    # Pre-encoded with ffmpeg so the check streams real G.711, with no encoder
    # of our own to get wrong. Both are 8 kHz, one byte per sample.
    "mulaw": SAMPLE.with_name("verify-sample-8k.ulaw"),
    "alaw": SAMPLE.with_name("verify-sample-8k.alaw"),
}


def load_sample(path: Path) -> tuple[bytes, int]:
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            sys.exit(f"verify: {path} must be mono 16-bit PCM")
        return w.readframes(w.getnframes()), w.getframerate()


def mint_token(host: str, api_key: str, ttl: int = 300) -> str:
    try:
        import requests
    except ImportError:
        sys.exit("verify: --token needs requests. pip install requests")
    r = requests.post(
        f"https://{host}/waves/v1/auth/token",
        json={"ttl_seconds": ttl},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=20,
    )
    if not r.ok:
        sys.exit(f"verify: FAIL minting token: HTTP {r.status_code} {r.text[:200]}")
    tok = r.json()["access_token"]
    print(f"  minted short-lived token, expires in {r.json()['expires_in']}s")
    return tok


async def run(args: argparse.Namespace) -> int:
    api_key = os.environ.get("SMALLEST_API_KEY")
    if not api_key:
        print("verify: FAIL SMALLEST_API_KEY is not set", file=sys.stderr)
        return 1

    # Match the customer's real audio format so the check exercises their path.
    if args.encoding in ("opus", "ogg_opus") and not args.sample:
        sys.exit(f"verify: --encoding {args.encoding} needs --sample with your own encoded file. "
                 f"ffmpeg -i in.wav -c:a libopus -b:a 32k -ar 16000 -ac 1 out.ogg")
    if args.encoding in ("opus", "ogg_opus"):
        asset = Path(args.sample)
        if not asset.exists():
            sys.exit(f"verify: {asset} not found")
        audio = asset.read_bytes()
        rate = int(args.sample_rate) if args.sample_rate else 16000
        bytes_per_sample = 1          # paced by byte count, not sample count
    elif args.encoding in TELEPHONY_SAMPLES:
        # G.711 is one byte per sample and already encoded, so nothing is read
        # from the 16 kHz WAV on this path. --sample takes a raw .ulaw/.alaw
        # file, which is how you check against your own call recording.
        rate = int(args.sample_rate) if args.sample_rate else 8000
        if args.sample:
            asset = Path(args.sample)
            if asset.suffix.lower() in (".wav", ".wave"):
                sys.exit(f"verify: --encoding {args.encoding} needs raw G.711 bytes, not a WAV. "
                         f"Convert first: ffmpeg -i {args.sample} -ar {rate} -ac 1 "
                         f"-f {args.encoding} out.{'ulaw' if args.encoding == 'mulaw' else 'alaw'}")
        else:
            asset = TELEPHONY_SAMPLES[args.encoding]
            if args.sample_rate and int(args.sample_rate) != 8000:
                sys.exit(f"verify: the bundled {args.encoding} sample is 8000 Hz, not {args.sample_rate}. "
                         "Pass --sample with your own raw G.711 file at that rate.")
            rate = 8000
        if not asset.exists():
            sys.exit(f"verify: {asset} not found")
        body = asset.read_bytes()
        silence = b"\xff" if args.encoding == "mulaw" else b"\xd5"
        audio = silence * int(rate * 0.3) + body + silence * int(rate * 1.0)
        bytes_per_sample = 1
    else:
        pcm, rate = load_sample(Path(args.sample) if args.sample else SAMPLE)
        if args.sample_rate and int(args.sample_rate) != rate:
            sys.exit(
                f"verify: cannot convert the sample from {rate} Hz to {args.sample_rate} Hz. "
                "Pass --sample with a WAV already at that rate."
            )
        audio = b"\x00\x00" * int(rate * 0.3) + pcm + b"\x00\x00" * int(rate * 1.0)
        bytes_per_sample = 2

    params = {
        "model": args.model,
        "language": args.language,
        "sample_rate": str(rate),
        "encoding": args.encoding,
        "format": "true",
        "punctuate": "true",
        "capitalize": "true",
        "itn_normalize": args.itn_normalize,
        "endpointing": args.endpointing,
        "finalize_on_words": args.finalize_on_words,
        "vad_events": args.vad_events,
    }
    if args.eou_timeout_ms is not None:
        params["eou_timeout_ms"] = str(args.eou_timeout_ms)
    if args.keywords:
        params["keywords"] = args.keywords
    if args.external_session_id:
        params["external_session_id"] = args.external_session_id
    for extra in args.param:
        k, _, v = extra.partition("=")
        params[k] = v

    if args.query_auth and not args.token:
        print(
            "verify: refusing to put a permanent API key in the URL. The query form is for "
            "short-lived tokens, which is what a browser should use. Add --token.",
            file=sys.stderr,
        )
        return 1
    credential = mint_token(args.host, api_key) if args.token else api_key
    url = f"wss://{args.host}/waves/v1/stt/live?{urlencode(params)}"
    print(f"→ wss://{args.host}/waves/v1/stt/live")
    for k, v in params.items():
        print(f"    {k}={v}")

    finals: list[str] = []
    errors: list[dict] = []
    partials = 0
    t0 = time.monotonic()
    ms = lambda: int((time.monotonic() - t0) * 1000)

    if args.query_auth:
        url += "&" + urlencode({"api_key": credential})
        headers: list[tuple[str, str]] = []
    else:
        headers = [("Authorization", f"Bearer {credential}")]

    try:
        async with websockets.connect(
            url, additional_headers=headers, max_size=10 * 1024 * 1024, open_timeout=20
        ) as ws:
            print(f"  connected in {ms()} ms")

            async def send() -> None:
                # 0.3 s lead-in, the sample, then 1.0 s so endpointing fires.
                step = int(rate * 0.04) * bytes_per_sample
                try:
                    for i in range(0, len(audio), step):
                        await ws.send(audio[i : i + step])
                        await asyncio.sleep(0.04)
                    await ws.send(json.dumps({"type": "close_stream"}))
                except websockets.ConnectionClosed:
                    # The server rejected the configuration and closed. recv() has the reason.
                    return

            async def recv() -> None:
                nonlocal partials
                async for msg in ws:
                    if not isinstance(msg, str):
                        continue
                    try:
                        d = json.loads(msg)
                    except ValueError:
                        continue
                    if d.get("type") == "error" or d.get("status") == "error":
                        errors.append(d)
                        return
                    text = (d.get("transcript") or "").strip()
                    if d.get("is_final"):
                        if text:
                            finals.append(text)
                            print(f"  [{ms():5d} ms] final: {text!r}")
                        if d.get("is_last"):
                            return
                    elif text:
                        partials += 1

            await asyncio.wait_for(asyncio.gather(send(), recv()), timeout=args.timeout)
    except asyncio.TimeoutError:
        if not errors:
            print(f"verify: FAIL no terminal response within {args.timeout}s", file=sys.stderr)
            return 1
    except websockets.InvalidStatus as e:
        code = e.response.status_code
        hint = {
            401: "bad or expired credential. Check SMALLEST_API_KEY, or mint a fresh token.",
            400: "the server rejected the request before the upgrade. Check `model`.",
            403: "this credential is not allowed on this route.",
        }.get(code, "")
        print(f"verify: FAIL HTTP {code} on the WebSocket upgrade. {hint}", file=sys.stderr)
        return 1
    except Exception as e:
        if not errors:
            print(f"verify: FAIL {type(e).__name__}: {e}", file=sys.stderr)
            return 1

    if errors:
        e = errors[0]
        print(f"verify: FAIL server rejected the configuration: {json.dumps(e)}", file=sys.stderr)
        if e.get("error_code") == "LANGUAGE_NOT_ENABLED_IN_REGION":
            print(
                f"  '{e.get('language')}' is not served from region {e.get('region')}. "
                "Use --host api.us.smallest.ai for zh/yue/ja/ko/multi-asian, "
                "or --host api.india.smallest.ai for ta/te/kn/ml/multi-south-indic.",
                file=sys.stderr,
            )
        return 1

    if not finals:
        print(
            "verify: FAIL connected and streamed audio but no transcript came back.\n"
            "  The connection works, so this is the audio path: check sample_rate and encoding "
            "match the audio you are sending.",
            file=sys.stderr,
        )
        return 1

    joined = " ".join(finals).lower()
    expect = [w.strip().lower() for w in args.expect.split(",") if w.strip()]
    missing = [w for w in expect if w not in joined]
    print(f"  {len(finals)} final(s), {partials} partial(s) in {ms()} ms")

    if missing:
        print(
            f"verify: FAIL transcript did not contain {missing}.\n"
            f"  got: {joined!r}\n"
            "  A connection this far means auth and parameters are fine. Check that the audio "
            "reaching us is the sample, at the declared sample rate.",
            file=sys.stderr,
        )
        return 1

    print("verify: OK")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="api.smallest.ai",
                   help="api.smallest.ai (default), api.us.smallest.ai, api.india.smallest.ai")
    p.add_argument("--language", default="en")
    p.add_argument("--model", default="pulse", choices=["pulse", "pulse-2"],
                   help="pulse is the recommended model for voice agents.")
    p.add_argument("--vad-events", default="true", choices=["true", "false"],
                   help="the profiles turn this on; the server default is false.")
    p.add_argument("--finalize-on-words", default="false", choices=["true", "false"],
                   help="the profiles turn this off; the server default is true.")
    p.add_argument("--encoding", default="linear16",
                   choices=["linear16", "linear32", "mulaw", "alaw", "opus", "ogg_opus"],
                   help="mulaw and alaw stream a pre-encoded 8 kHz sample, so a telephony "
                        "configuration is tested as it will actually run.")
    p.add_argument("--sample-rate", default=None,
                   help="8000 for telephony, which the bundled mulaw and alaw samples already are.")
    p.add_argument("--eou-timeout-ms", type=int, default=None,
                   help="leave unset unless you have measured a reason. Below 500 splits words.")
    p.add_argument("--endpointing", default="true", choices=["true", "false"],
                   help="server default is true.")
    p.add_argument("--itn-normalize", default="false", choices=["true", "false"],
                   help="server default is false. Pass what you are shipping.")
    p.add_argument("--keywords", default="")
    p.add_argument("--external-session-id", default="")
    p.add_argument("--param", action="append", default=[], metavar="K=V",
                   help="any additional query parameter, repeatable")
    p.add_argument("--token", action="store_true", help="mint and use a short-lived access token")
    p.add_argument("--query-auth", action="store_true",
                   help="send the credential as ?api_key= instead of a header (what a browser does)")
    p.add_argument("--sample", help="your own audio instead of the bundled sample: a mono "
                                    "16-bit PCM WAV, or raw G.711 bytes with --encoding mulaw/alaw")
    p.add_argument("--expect", default=DEFAULT_EXPECT,
                   help="comma-separated words the transcript must contain. Empty disables the check.")
    p.add_argument("--timeout", type=float, default=45)
    return asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
