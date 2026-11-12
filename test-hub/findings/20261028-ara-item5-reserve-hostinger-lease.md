# ARA item 5 — signed reserve Vercel wake integration
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / anthares-ara-vercel-reserve
DATE: 2026-10-28
RUN: pending
JOB: ARA canonical Cloudflare gateway /v1/mcp/execute
COMMIT: 6599ba3b0e9cc8ddf06b4a8811b28f7f6f811ed3
SUPERSEDES: item5-primary-Hostinger partial finding

## BASELINE_PROVEN
Canonical Cloudflare gateway connects to https://anthares-ara-vercel-reserve.vercel.app and the standby URL, both served by Vercel project prj_i5ylgY1BgnrPZzSoBZ5UMOtJX77P. Production READY dpl_FmurJGjaAQTfrKAQnEFGFS76TKh3; app source is non-Git deploy with api/router.js, api/mcp.js, api/bootstrap.js, package.json and vercel.json. Owner has authorized using the already-authenticated browser to recover exact source. Hostinger authenticated broker has sequence=1 from preproduction manual proof. Separate anthares-remote-primary project is already modified but is not the gateway's signed execute target.

## SCOPE / EXCLUSION
Create canonical source snapshot and minimal wake-only emission after successful INSERT in api/mcp.js, and if necessary enqueue in api/router.js, preserve Ed25519 signature validation, replay, OAuth, Neon leases/fences, idempotency and device status. Secret ARA_WAKE_NOTIFY_SECRET protected in Production; enabled flag defaults OFF. No modifications to Windows C8, Cloudflare gateway, publishers, Neon schema, main or concurrent PR branches. Keep existing Vercel deployment available to roll back.

## SUCCESS_SIGNAL
Source matches browser original and available deployment response prefix. Unit test of fail-open, one pulse per new queued job, no pulse on duplicate. New reserve deployment READY and healthz 200, Cloudflare signed command done, Hostinger state sequence increments with broker-recognized HTTP 202. If no increment, report PARTIAL and do not claim success.
