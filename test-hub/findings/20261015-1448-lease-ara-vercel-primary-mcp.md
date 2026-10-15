# Lease — Anthares Remote Vercel/Neon ChatGPT-facing MCP primary

STATUS: RUNNING
AREA: architecture
DATE: 2026-10-15
RUN: none
JOB: none
COMMIT: baseline bbf00bbb3f75b8b6f809c6d46e6617ac71e0d51e
SUPERSEDES: none

## Objetivo
Migrate the ChatGPT-facing Anthares Remote MCP primary away from the Cloudflare OAuth ingress to Vercel + Neon, while preserving GitLab/GitHub recovery queues and Cloudflare only as later redundancy.

## BASELINE_PROVEN
- `test-hub/findings/20261015-ara-gitlab-primary-proven.md`: real Anthares Remote command roundtrip via GitLab private issue queue is proven.
- `test-hub/findings/20261015-ara-primary-migration-plan.md`: Vercel + Neon is the intended low-latency ChatGPT-facing replacement candidate.
- Vercel `anthares-ara-vercel-reserve` production deployment is READY and Neon `anthares-ara-ha` contains reserve/fencing tables.
- Current ChatGPT Cloudflare plugin authorization is invalid/expired after repeated reconnect attempts.

## FAILED_AVOIDED
- Do not repeat Cloudflare OAuth reconnect as the primary recovery strategy; the user-defined retry threshold has been exceeded.
- Do not depend on Cloudflare Durable Objects or the Cloudflare signing-key endpoint in the new primary path.
- Do not use Render, TinyFish, Browserless, WinRemote, MeshCentral or CircleCI.

## SUCCESS_SIGNAL
1. New Vercel primary endpoint returns healthy OAuth/MCP metadata without Cloudflare dependency.
2. Windows Anthares Remote Agent heartbeats/polls the Vercel+Neon primary after controlled agent-only cutover.
3. A real `ping` command completes through Vercel+Neon and returns `pong`.
4. The new endpoint is suitable as the ChatGPT development plugin `/mcp` URL.

## FAILURE_SIGNAL
- Vercel deployment cannot provide OAuth/MCP protocol required by ChatGPT, or the Windows agent cannot complete a real Vercel+Neon roundtrip.

## TEST_VALIDITY
- No result counts unless the deployed Vercel endpoint, Neon rows, and agent roundtrip all correspond to the same new primary deployment.
- No PC reboot is permitted in this lease.

Lease expires no later than 2026-10-15 15:18 -04:00.