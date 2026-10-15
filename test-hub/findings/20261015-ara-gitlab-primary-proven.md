# Anthares Remote migrated off Cloudflare primary

STATUS: PROVEN
AREA: architecture
DATE: 2026-10-15
RUN: GitLab private queue issues 7-10
JOB: ara-restore-system-task-gitlab-20261015-1258; ara-promote-gitlab-primary-20261015-1304; ara-gitlab-primary-proof-20261015-1307; ara-read-transport-mode-20261015-1307
COMMIT: c8768572cfc9cd1b5cf99a09a1c6554e3b8e9ec7
SUPERSEDES: test-hub/findings/20261015-ara-primary-migration-plan.md

## Result
Cloudflare Durable Objects write quota blocked the previous MCP/OAuth path. Anthares Remote control was moved to the already-supported private issue-queue transport without waiting for quota reset.

Current routing:
1. GitLab private issue queue — primary.
2. GitHub private issue queue — secondary redundancy.
3. Vercel + Neon — reserve infrastructure, not yet promoted because direct agent roundtrip has not been proven.
4. Cloudflare HTTP/MCP — tertiary redundancy only after quota recovery and write-amplification fixes.

## Decisive evidence
- GitLab issue #7 executed the canonical SYSTEM scheduled-task repair successfully. Result: `Anthares Remote Agent SYSTEM` running/enabled, principal SYSTEM, boot trigger, restart_count 999, watchdog disabled.
- GitLab issue #8 applied and persisted the queue-primary routing mode.
- GitLab issue #9 returned `pong` after promotion.
- GitLab issue #10 read `transport-mode.json` and confirmed `primary=gitlab_private_issue_queue`, `secondary=github_private_issue_queue`, `tertiary=cloudflare_http_control`, `cloudflare_http_active=false`.

## Consequence
Do not treat Cloudflare as Anthares Remote primary. Do not wait for its quota reset to operate the remote. Continue using the Anthares Remote surface through the GitLab private queue. Preserve GitHub as first redundancy. Vercel+Neon can be promoted only after practical command roundtrip to the Windows agent. Cloudflare requires quota recovery plus heartbeat/OAuth write-amplification corrections before becoming eligible again.
