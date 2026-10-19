# Claude — Anthares instructions

This repository participates in a distributed system. Claude must read `AGENTS.md` and `test-hub/README.md` before changing any code, configuration, documentation, tests, or infrastructure.

## Scope and coordination
- GitHub is the canonical repository; GitLab is a peer. Read both current versions before any edit or mirror operation.
- Acquire a valid nonconflicting Test Hub lease for every mutation; check active findings and relevant CI jobs.
- Change only an isolated branch and propose a pull request. Keep `main` unchanged until the user authorizes integration and checks pass.
- Before writing, refresh destination HEAD and target blob SHA. Use optimistic concurrency. Abort on stale HEAD or changed target.
- Log decisive evidence in the Test Hub; do not infer successful production publication from enqueue, upload, or a green CI status.
- Do not reproduce credentials, tokens, session files, secrets, cookies, or identifying owner login data in messages, logs, commits or prompts.

## Anthares architecture
- Anthares Remote (ARA): authorized Windows control plane; do not bypass the signed ARA boundary or manually impersonate its identity.
- Anthares Browser: isolated profile, hidden and muted when a browser operation is explicitly authorized; never attach to a personal Chrome window.
- CORTES: physical Android is the principal Kwai publisher; MEmu4 is an automatic fallback, never a competing simultaneous executor. Respect dedupe and independent post confirmation.
- Preserve Anthares Android Runtime SYSTEM authority and separate interactive fallback; avoid uncontrolled dual execution.
- Do not reboot, shut down, log off, reset queues, delete masters, clear uncertain jobs, or rotate credentials without explicit owner authorization.
- Do not use retired WPVibe, TinyFish, MeshCentral or Remote Desktop Commander paths.
- Never use paid providers, billing activation or a credit card without explicit owner authorization.
- Keep independent work scoped: a code-review task must not start a real Kwai/TikTok publication as an audit probe.

## Claude Free connector state
- Claude.ai Free supports one remote custom MCP connector. Staged OAuth grants `ara.read`, `github.read`, and narrowly scoped `github.write` when requested; Claude never receives `ara.write`. Deployment and owner OAuth approval remain necessary.
- Current production MCP and its ChatGPT client pin must be preserved.
- The built-in Claude GitHub content connector is context/read oriented; it is not equivalent to a GitHub write agent.
- GitHub tools are staged in `cloudflare-ara-mcp/src/github-bridge.mjs`; writes remain blocked until Cloudflare receives the server-side secret `ANTHARES_GITHUB_TOKEN`. Only approved repositories, `claude/*` branches, live Test Hub leases, expected HEAD/file SHA and draft PRs are authorized.
- Never claim integration completed based only on source code, a branch, or PR.
