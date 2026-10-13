# ARA v4 dual-transport proof — 2026-10-13

Status: **PROVEN** on `DESKTOP-FTDK0HP`.

## Cloudflare transport

`anthares-remote-agent-v4.exe` was launched for the canonical device and the connected ChatGPT `Anthares Remote Cloudflare` MCP continued to return fresh heartbeats and real `remote_exec` results with exit code 0. The active Cloudflare controller was `https://anthares-ara-backup.anthares1.workers.dev`.

## GitHub private issue queue transport

Repository: `UniversoAnthares/anthares-ara-queue` (private).

1. Issue #4 targeted temporary device `DESKTOP-FTDK0HP-QUEUE-TEST` with `type=ping`. v4 removed `ara-queued` and posted `ok=true, output=pong`.
2. Issue #5 targeted canonical device `DESKTOP-FTDK0HP` with `type=ping`. v4 removed `ara-queued` and posted `ok=true, output=pong`.
3. Issue #6 targeted canonical device with `type=process_kill` for the duplicate legacy agent PID 7840. v4 returned `ok=true` and `status=terminated`; process inspection afterward showed only v4.
4. Issue #7 targeted the stale supervisor with `type=shell`; the supervisor process was absent in the subsequent process inspection.

This proves the v4 issue queue is not a contract-only test: it executed real command classes on the authorized PC independently of the Cloudflare MCP request path.

## Runtime selection consequence

The user fallback must prefer `anthares-remote-agent-v4.exe` once a local `v4-validated.flag` exists. It may fall back to `anthares-remote-agent.exe` only if v4 is absent or explicitly rolled back. Automatically killing a validated v4 in order to prefer legacy would remove the full GitHub queue recovery transport.

## Separate transport check

Both canonical Cloudflare origin and reserve proxy accepted authenticated heartbeat for `DESKTOP-FTDK0HP` with HTTP 200; reserve response carried `x-anthares-ara-route: reserve-proxy`.

## Remaining privilege boundary

Creating the `Anthares Remote Agent SYSTEM` ONSTART task from the non-elevated remote session returned Windows `Access denied`. Until an elevated task installation is performed, the hidden `Anthares Remote Agent User` task remains the live watchdog. Do not attempt UAC bypass.
