# Forgejo recovered; GitLab remains at OAuth consent
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: bf550eb2332afefa965511b7e183596692e28fd4
SUPERSEDES: none

## Baseline
Forgejo redundancy had been PROVEN earlier at anthares.us/forgejo; GitLab MCP config existed in ~/.codex/config.toml.

## Discovery
Forgejo public endpoint returned HTTP 502. Host inspection showed no running Forgejo process and a stale Unix socket. Hostinger account exposes no crontab, systemd, tmux, screen or supervisord, so daemon restart cannot currently be delegated to a native process supervisor.

## Recovery
Removed stale socket, restarted Forgejo from persistent Hostinger storage, invoked fixed sync endpoint, and compared external refs.

## Evidence
Forgejo API returned version 15.0.9+gitea-1.22.0.
After recovery GitHub and Forgejo both returned main SHA 96decc9115e41457f8444c5f965f12dba83f53b1 and EQUAL=True.
A keepalive script was versioned at tools/forgejo_keepalive.sh (commit bf550eb2332afefa965511b7e183596692e28fd4), but native cron installation is unavailable on this Hostinger shell; do not claim watchdog PROVEN.

## GitLab
Codex config still contains [mcp_servers.GitLab] url=https://gitlab.com/api/v4/mcp. ChatGPT plugin catalog still has no GitLab/Forgejo connector. GitLab MCP therefore requires external OAuth consent in the configured MCP client before repository operations can be proven.

## Consequence
Preserve current Forgejo data/proxy/sync. Treat repository redundancy as operational with a daemon-liveness caveat. Next action requiring the user: approve GitLab MCP OAuth in browser. After approval, immediately test GitLab project creation/import, mirror, branch, commit, CI and SHA convergence. For Forgejo agent access, use a dedicated MCP/API credential path; never expose the existing server token in Hub/logs.
