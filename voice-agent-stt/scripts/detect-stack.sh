#!/usr/bin/env bash
# Detect the voice-agent stack in a repo.
#
#   detect-stack.sh [root]
#
# Line 1: livekit | pipecat | node-ws | python-websockets | browser | unknown
# Line 2: stt=<provider>  when an existing STT provider is wired, else stt=none
#
# Searches dependency manifests and lock files at the root and up to three
# directories deep, so a monorepo with the agent under services/ is found.

set -eu

root="${1:-.}"
cd "$root"

MANIFESTS='package.json requirements.txt requirements-*.txt pyproject.toml poetry.lock uv.lock Pipfile Pipfile.lock pnpm-lock.yaml yarn.lock package-lock.json setup.py setup.cfg environment.yml'

# Collect candidate files at depth <= 3, skipping vendor directories.
manifest_files() {
  local pat
  for pat in $MANIFESTS; do
    find . -maxdepth 4 -name "$pat" -not -path '*/node_modules/*' -not -path '*/.venv/*' \
      -not -path '*/venv/*' -not -path '*/site-packages/*' -not -path '*/.git/*' \
      -not -path '*/dist/*' -not -path '*/build/*' 2>/dev/null || true
  done
}

FILES="$(manifest_files)"

in_manifests() {
  [ -n "$FILES" ] || return 1
  printf '%s\n' "$FILES" | tr '\n' '\0' | xargs -0 grep -sqE "$1" 2>/dev/null
}

# Source files, for import-based detection when a manifest does not name the dep.
in_sources() {
  grep -rsqE "$1" --include='*.py' --include='*.ts' --include='*.tsx' --include='*.js' \
    --include='*.jsx' --include='*.mjs' . \
    --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=venv \
    --exclude-dir=site-packages --exclude-dir=.git --exclude-dir=dist --exclude-dir=build 2>/dev/null
}

# ---- stack -----------------------------------------------------------------
stack=unknown

if in_manifests 'livekit-agents|livekit\.agents|"@livekit/agents"|livekit-plugins' || in_sources 'from livekit|import livekit|@livekit/agents'; then
  stack=livekit
elif in_manifests 'pipecat-ai|pipecat_ai' || in_sources 'from pipecat|import pipecat'; then
  stack=pipecat
elif in_manifests '"ws"[[:space:]]*:|@types/ws' || in_sources "require\\(['\"]ws['\"]\\)|from ['\"]ws['\"]"; then
  stack=node-ws
elif in_manifests 'websockets' || in_sources '^import websockets|^from websockets'; then
  stack=python-websockets
elif in_sources 'navigator\.mediaDevices|getUserMedia|new AudioContext|AudioWorklet'; then
  stack=browser
fi

# A browser audio path inside a Node repo still needs the token flow.
if [ "$stack" = "node-ws" ] && in_sources 'navigator\.mediaDevices|getUserMedia'; then
  stack=browser
fi

echo "$stack"

# ---- existing STT provider -------------------------------------------------
provider=none
for p in deepgram assemblyai speechmatics gladia rev_ai cartesia; do
  if in_manifests "$p" || in_sources "$p"; then provider="$p"; break; fi
done
if [ "$provider" = none ]; then
  if in_manifests 'openai-whisper|faster-whisper' || in_sources 'whisper'; then
    provider=whisper
  elif in_sources 'speech_v1|SpeechClient|google\.cloud\.speech'; then
    provider=google
  elif in_sources 'azure\.cognitiveservices\.speech|SpeechRecognizer'; then
    provider=azure
  fi
fi

echo "stt=$provider"
