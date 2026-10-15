# Anthares Remote primary migration — emergency plan

STATUS: RUNNING
AREA: architecture
DATE: 2026-10-15

## Goal
Move Anthares Remote primary control away from Cloudflare immediately after Durable Objects write quota exhaustion.

## Target routing
1. Primary: GitHub private issue queue already polled by the SYSTEM Anthares Remote Agent.
2. Secondary: Vercel control surface backed by Neon Postgres; current Vercel reserve deployment and Neon `anthares-ara-ha` are live infrastructure to be promoted only after practical proof.
3. Tertiary: Cloudflare MCP/control after quota recovery and write-amplification fixes.
4. Additional reserve: GitLab private issue queue remains supported by the SYSTEM supervisor when credentials are present; GitLab CI quota is separate and does not retire the API queue transport.

## Safety
- Do not reboot until `Anthares Remote Agent SYSTEM` startup task is positively proven present/enabled with SYSTEM + AtStartup + Highest.
- Keep `Anthares Remote Recovery Watchdog` disabled.
- Do not alter MEmu4/Kwai production while restoring remote control.
- Preserve one executor and existing fencing/dedup semantics.

## Current evidence
- SYSTEM supervisor source explicitly treats private GitHub/GitLab issue queues as recovery authority when HTTP is unavailable.
- Vercel access is restored and `anthares-ara-vercel-reserve` production deployments are READY.
- Vercel reserve already points at Neon via `DATABASE_URL`; Neon contains fencing/reserve tables.
- Cloudflare OAuth reconnect currently fails with Durable Objects free-tier row-write exhaustion.

## Immediate actions
1. Restore canonical SYSTEM startup task through the existing private issue queue.
2. Prove GitHub private issue queue command roundtrip without Cloudflare.
3. Promote the issue queue transport to primary operational routing.
4. Build/validate Vercel+Neon as low-latency secondary and ChatGPT-facing MCP replacement.
5. Patch Cloudflare heartbeat/OAuth write amplification before returning it as tertiary redundancy.
