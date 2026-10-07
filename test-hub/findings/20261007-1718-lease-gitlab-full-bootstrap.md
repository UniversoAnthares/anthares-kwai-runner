# Lease - GitLab full bootstrap and provider redundancy
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-08
BASELINE: d68ceb3797d00a9efc52abf438355413ca992ecb
EXPIRES: 30 minutes from creation

## Objective
Complete GitLab project synchronization, provider redundancy, and automatic mirroring without exposing credentials.

## Preserve
- Provider router tests already PROVEN.
- Existing GitLab MCP/project findings remain historical evidence.
- No force-push on divergence without validation.
- No secrets in Git, logs, command output, or repository URLs.

## Avoid
- GitHub-Actions-only mirroring as the sole failover path.
- Old AUTH_REQUIRED conclusions without retesting after the newly created GitLab API credential.
