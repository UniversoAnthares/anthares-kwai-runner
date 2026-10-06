# Cloudflare control TikTok OIDC deploy — PROVEN
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37418647980
JOB: none
COMMIT: c03b92c7e16fdd5295a6c4489318daacf1862962
SUPERSEDES: test-hub/findings/20261006-0522-lease-cloudflare-control-tiktok-oidc-deploy.md

## Objective
Deploy and verify the reviewed TikTok GitHub OIDC allowlist fix without changing queue semantics.

## Result
PROVEN. A fresh clone of current main was deployed through Wrangler OAuth from the authorized console. Public /health remained healthy on queue-fencing-v16 with persistent_state=true, queue_bound=true and pc_fallback=false. The independent read-only TikTok Central Session Read Probe then completed SUCCESS using GitHub OIDC against the protected central-session endpoint.

## Decisive evidence
Run 37418647980 completed success after the deploy. Before the deploy, TikTok Real Publish run 37416752186 failed at the first protected queue call with HTTP 401 immediately after obtaining GitHub OIDC. The post-deploy protected central-session read no longer receives 401.

## Consequence
The deployed-control HTTP 401 blocker is closed. Do not reopen Cloudflare OIDC deployment. TikTok publish work may continue from its current serialized tiktok-publish lease and must preserve the proven queue/fencing/confirmation gates.
