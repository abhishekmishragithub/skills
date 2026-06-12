# Smallest AI Agent Skills

Agent Skills for building with [Smallest AI](https://smallest.ai) — ultra-fast text-to-speech, speech-to-text, and voice AI. These skills follow the [Agent Skills specification](https://agentskills.io/specification) and work with Claude Code, Cursor, and any compatible AI coding assistant.

## Installation

```bash
npx skills add smallest-inc/skills
```

## Available Skills

| Skill | Description |
|---|---|
| [text-to-speech](./text-to-speech) | Generate 44.1 kHz speech with Lightning v3.1 / v3.1 Pro — 12 languages, voice cloning, ~100ms streaming |
| [speech-to-text](./speech-to-text) | Transcribe audio with Pulse (38 languages, 64ms TTFT streaming) and Pulse Pro (leaderboard-ranked English) |
| [setup-api-key](./setup-api-key) | Obtain and configure a Smallest AI API key |

More coming: voice agents (Atoms), speech-to-speech (Hydra), LLM (Electron).

## Configuration

All skills require a Smallest AI API key:

```bash
export SMALLEST_API_KEY="your-api-key"
```

Get one at [app.smallest.ai/dashboard](https://app.smallest.ai/dashboard) → Developer → API Keys, or run the `setup-api-key` skill.

## Current models

| Product | Current model | Deprecated |
|---|---|---|
| TTS | `lightning_v3.1` (default), `lightning_v3.1_pro` | `lightning-v2`, `lightning-large` |
| STT | `pulse`, `pulse-pro` | — |

## SDKs & Integrations

- **Python** — `pip install smallestai`
- **JavaScript/TypeScript** — `npm install smallestai`
- **Vercel AI SDK** — [smallest-ai-vercel-provider](https://github.com/smallest-inc/smallest-ai-vercel-provider)
- Also: [LiveKit](https://docs.smallest.ai/atoms/integrations/live-kit), [Pipecat](https://docs.smallest.ai/atoms/integrations/pipecat), [n8n](https://docs.smallest.ai/atoms/integrations/n-8-n), and [more](https://docs.smallest.ai/atoms/developer-tools/overview)

## Documentation

Full docs: [docs.smallest.ai](https://docs.smallest.ai) — every page is AI-readable by appending `.md` to its URL. MCP server: `https://docs.smallest.ai/_mcp/server`

## License

MIT
