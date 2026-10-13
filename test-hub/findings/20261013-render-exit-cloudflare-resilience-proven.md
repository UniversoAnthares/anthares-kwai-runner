# 2026-10-13 — Render-independent resilience path PROVEN

## Changes
- `tools/anthares_resilience.py` no longer defaults to a Render browser. The persistent/on-demand browser route is `https://anthares-reserva-browser.anthares1.workers.dev` and GitHub Actions is the finite-job emergency executor.
- `.github/workflows/anthares-resilience-watchdog.yml` no longer references a Render browser endpoint.
- `anthares-remote-agent/windows/run-agent-system-supervisor.ps1` was changed in source so Cloudflare ARA backup is primary, `anthares-control` is secondary, and an optional third control can be injected later. Render is absent from the canonical supervisor source.
- A false-negative health check was corrected: `anthares-ara-backup` exposes `/healthz`, not `/health`.

## Practical proof
GitHub Actions run `38409604968` completed successfully. Its live checks reported:
- `continuity_ok=true`
- `ok=true`
- `render_required=false`
- `degraded=false`
- browser route: `anthares-reserva-browser`
- reserve route: `cloudflare-ara`
- `https://anthares-ara-backup.anthares1.workers.dev/healthz` -> HTTP 200, Cloudflare Durable Object SQLite, persistence cycle true, independent of Render Postgres true.
- `https://anthares-control.anthares1.workers.dev/health` -> HTTP 200.
- `https://anthares-control.anthares1.workers.dev/failover-self-test` -> HTTP 200.
- `https://anthares-reserva-browser.anthares1.workers.dev/health` -> HTTP 200.

## Remaining boundary
The currently connected ChatGPT Anthares Remote MCP gateway is still the Render-hosted connector path. Control/browser continuity is now independently proven through Cloudflare + GitHub Actions, but complete removal of Render from the ChatGPT connector still requires an independent MCP Streamable HTTP + OAuth gateway and then repointing/reconnecting the ChatGPT connector to it. Do not declare that final gateway migration complete until a real tool execution succeeds through the non-Render MCP URL.
