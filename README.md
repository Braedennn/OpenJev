# OpenJev

OpenJev is a **Jev-governed agent harness**: a desktop AI agent that consults
[TypeSafe's Jev](https://typesafe.ai) decision model at every thinking step,
so its routing, verification, and judgment come from calibrated probabilities
instead of vibes.

It is a fork of [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
(`dsh`), rebranded and extended. OpenJev is not affiliated with or endorsed by
DeepSeek.

## What makes it OpenJev

- **Jev on every step** — a host plugin hooks `agent/pre-step` and asks Jev what
  the agent should do next (`act` / `gather` / `clarify` / `verify`) with a
  probability distribution. The decision is injected into the step as a plugin
  notice, and every consultation is appended to a trace log as proof.
- **Jev tools for the model** — `jev_ask`, `jev_verify`, `jev_screen`,
  `jev_classify`, `jev_route`, `jev_trace`.
- **Correct question formatting** — the plugin builds every `noul` / `choice` /
  `score` question in the exact shape Jev expects before calling the TypeSafe
  endpoint directly.
- **Trace log** — `%USERPROFILE%\.openjev\trace.jsonl` records every Jev call:
  source (`agent/pre-step:turn=1 step=2`), latency, probabilities, usage.

## Requirements

- Windows 10/11 x64
- Node.js 22.19+ (24 LTS recommended) and pnpm 11+ for building from source
- No daemon, no environment files: the app calls the TypeSafe endpoint directly

## Build the desktop app

```sh
pnpm install
pnpm run build
pnpm package:desktop:win:x64:unsigned
```

Outputs (under `apps/desktop/.desktop-build/targets/win-x64/unsigned-artifacts/`):

- `openjev-<version>-win-x64.exe` — the installer
- `win-unpacked/OpenJev.exe` — portable, no install

The unsigned build triggers Windows SmartScreen on first run
("More info" → "Run anyway"). To run from source without packaging:

```sh
pnpm start:desktop
```

## Run

1. Launch `OpenJev.exe` (or `OpenJev.cmd`).
2. Add your Jev API key in **Settings → Models → Jev (decision layer)**.
   It is stored in `%USERPROFILE%\.dsh\.credentials.yaml` under the `openjev`
   reference and read live — no restart, no committed file.
3. Add any model provider (DeepSeek, OpenAI, Anthropic, OpenRouter, a local
   server, or any OpenAI-compatible gateway) in **Settings → Models → Add
   provider**.

## Releases

The EXE is built by GitHub Actions and attached to GitHub Releases — binaries
are never committed to the repository.

- Push a tag (`git tag v0.1.6-alpha.2 && git push origin v0.1.6-alpha.2`) and
  the `release` workflow builds the installer and attaches it to the release,
  together with the `blockmap` and a portable ZIP of `win-unpacked/`.
- Run the `release` workflow manually (Actions → release → Run workflow) to
  get the same files as downloadable workflow artifacts.

The build is unsigned, so Windows SmartScreen warns on first run
("More info" → "Run anyway").

## Repository layout

```
harness/          dsh fork with OpenJev branding and the Jev plugin
harness/openjev-plugin/   the Jev conductor plugin (host side)
openjev/          optional Python Jev client, CLI, and MCP server
tests/            Python tests for the optional bridge
tools/            rebrand tooling used to create this fork
OpenJev.cmd       launcher for the desktop app
```

## Optional: CLI and MCP

The Python package in this repository is a convenience for command-line and MCP
use; the desktop app does not need it. It reads the same key the Settings card
stores:

```sh
pip install -e .
jev classify "The invoice total is wrong" --labels billing,bug,feature
openjev            # MCP server over stdio (tools: jev_ask, jev_verify, ...)
```

## License

MIT. OpenJev is a modified fork of DeepSeek Harness (MIT, Copyright DeepSeek);
upstream license and notices are retained in `harness/LICENSE` and
`harness/THIRD_PARTY_NOTICES.md`. See `LICENSE` for the OpenJev notice.
