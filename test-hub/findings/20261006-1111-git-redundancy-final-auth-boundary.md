# Git redundancy — final autonomous boundary at OAuth/agent credential
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: a49670d4d2a99790
COMMIT: d534380732de82a124a6093414a9163b66e9a3de
SUPERSEDES: none

## Result
PROVEN: Forgejo public API remains live (15.0.9+gitea-1.22.0) and external git ls-remote still reads anthares-kwai-runner.
PARTIAL: Forgejo repository mirror remains operational with daemon-liveness caveat from 20261006-1058.
PARTIAL: dedicated Forgejo agent credential creation was attempted through the authorized remote-command path but was blocked by the platform safety layer before execution. No credential was exposed or created through that attempt.
PARTIAL: GitLab MCP OAuth was resumed in Codex as job a49670d4d2a99790 and is waiting for browser consent. GitLab official MCP uses OAuth and requires the user to review/approve the authorization request on first connection.

## Preserve
Keep anthares.us/forgejo, persistent Forgejo data, proxy, sync endpoint and existing mirror. Never expose or reuse the server-admin token in chat/logs.

## Avoid
Do not retry GitLab SSH until a new credential exists. Do not bypass the safety layer to extract/create tokens through chat-visible command output. Do not use Quick Tunnel.

## Human gate
Approve the GitLab OAuth authorization page opened by the MCP client. For Forgejo agent write access, connect a dedicated credential through a secret-bearing connector/configuration surface rather than returning the token through chat tooling.

## After gate
Immediately test GitLab project import/mirror, clone, branch, commit, GitLab CI and SHA convergence. Then test Forgejo agent read/branch/commit through the connected credential and close the acceptance flags.

## Lease closure
Lease 20261006-1109-lease-architecture-git-redundancy-agent-access.md is closed at this external authorization/security boundary.
