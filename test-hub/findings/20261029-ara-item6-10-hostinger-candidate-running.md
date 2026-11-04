# ARA fixed items 6 + 10 — candidate source and full-agent CI
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / Windows event subscriber
DATE: 2026-10-29
RUN: GitHub Actions CI pending
JOB: candidate branch feature/ara-item6-10-hostinger-fallback-20261029
COMMIT: refer to branch HEAD; base main e796883c36f25c20fabad2fa522c5286a14a713b
SUPERSEDES: none

## Scope
Integrate existing reviewed Hostinger read-only wake listener and automatic return to legacy 2-second polling into canonical Go agent. CI covers full Go regression/race/vet and Windows amd64 cross-compile. Wake-enabled mode reconciles every 12 seconds; network/HTTP/JSON errors restore 2-second polling. Normal heartbeat, mutex, leases, result replay, GitHub/GitLab private queues and broker authority remain unchanged.

## Gates
Source branch is not production. No token is included and no Windows process or binary is changed. Never claim item 6 or item 10 complete without full CI success and live Windows deployment/fallback proof. Existing security gate for canonical Windows agent replacement remains independent of repository branch rights.
