# Claude — Anthares instructions

## Permanent owner rule — agent-owned window lifecycle (2026-10-21)
Any temporary window, tab, console, dialog or emulator GUI created by Claude, Claude Code or a delegated agent MUST be closed immediately after its use (success, error, timeout, cancellation). Register PID and window/tab ownership; close in `finally`; recover only positively identified orphaned resources. Preserve the owner's personal windows and active shared browser/VM services. Keep automation invisible and silent. See [AGENTS.md](AGENTS.md) and canonical https://github.com/UniversoAnthares/home/blob/main/AGENTS.md. Propagate to subagents and run verification.


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
- Avoid retired WPVibe and TinyFish integrations. For authorized Windows administration, consult `docs/REMOTE_CONTROL_PRIORITY.md` and use Anthares Remote, WinRemote, Remote Desktop Commander, MeshCentral, then AI Commander.
- Never use paid providers, billing activation or a credit card without explicit owner authorization.
- Keep independent work scoped: a code-review task must not start a real Kwai/TikTok publication as an audit probe.

## Claude Free connector state
- Production endpoint: `https://anthares-ara-mcp.anthares1.workers.dev/mcp`. Owner authorization uses exact GitHub numeric identity, PKCE and one-use codes; email delivery is not an integration dependency.
- Real owner-authorized Claude Free tool acceptance is recorded in `test-hub/findings/20261019-1216-claude-mcp-real-acceptance-proven.md`; integration PR162 is merged. Read newer findings before relying on historical partial states.
- Claude receives `ara.read`, `github.read`, and narrowly scoped `github.write`; it never receives unrestricted `ara.write`. Existing ChatGPT access remains preserved.
- GitHub tools require approved repositories, `claude/*` branches, live Test Hub leases, expected HEAD/file SHA and draft PRs. The protected server-side credential remains only in Cloudflare.
- `run_tests` executes only the reviewed `mcp-regression` suite through Anthares Remote at the pinned deployed source SHA. Supply a unique UUID request_id. The service records a Test Hub lease/result, rejects replay and arbitrary commands, and returns the tested SHA and pass/fail evidence. It does not execute unreviewed branch code or publication operations.
- A disconnected device or failing test is a real operational failure to diagnose; never claim success from a tool catalogue or source publication alone.
- PR164 is a disposable acceptance draft and must not be merged.
