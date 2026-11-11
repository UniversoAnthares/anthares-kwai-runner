# AOI #7 / AOI-01 — Forgejo keepalive safe recovery source fixed
STATUS: PARTIAL
AREA: architecture/forgejo-daemon-hostinger-keepalive
DATE_UTC: 2026-11-11
OWNER: chatgpt-forgejo-keepalive-20261110
LEASE: CLOSED
SUPERSEDES: 20261110-forgejo-keepalive-safe-recovery-lease.md
GOVERNANCE_SHA: 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
SOURCE_SHA_BEFORE: 0170eb85c15e1ab8a882e08be0ee68e460632bd6
SOURCE_SHA_AFTER: 966e539447a814da72f8db0c8a682cef1603fe0b
BRANCH: fix/forgejo-keepalive-safe-recovery-20261110
PEER_GITLAB: project 87307248 holds the old same-content keepalive, intentionally not reset/overwritten.

## Actual changes
- Keepalive checks local Unix socket three times before attempting recovery.
- If an existing Forgejo web process is alive but unhealthy, it halts with explicit error 70 and preserves the process/socket; no competing second daemon.
- With no Forgejo process, removes only a stale Unix socket; refuses symlinks or regular files (exit 73).
- A held flock returns explicit temporary failure 75, instead of false success.
- Validates local installation, logs health/recovered PID and checks new process liveness for at most 20 seconds.
- This existing-script-only patch leaves WordPress, credentials, media, TikTok, Neon, mirror refs, deployment and existing Hostinger cron unchanged.

## Independent local synthetic QA
MODE: OpenAI ephemeral Linux test container; isolated HOME/Unix sockets/processes; no Hostinger connection, no real credentials.
COMMAND: bash -n tools/forgejo_keepalive.sh; Python unittest 7 cases.
RESULT: BASH_SYNTAX_PASS and 7/7 unittest PASS in 9.237 seconds. Cases: healthy no-op, stale socket starts exactly one daemon, regular file preserved, lock contention explicit, existing unhealthy process preserved, missing binary fails closed, symlink preserved.
FILE: tests/test_forgejo_keepalive_safety.py
NO_MEDIA: true
NO_PUBLICATION: true
NO_ADDITIONAL_COST: true

## Operational truth and outstanding
GitHub source is fixed after merge only. The Hostinger Anthares Remote advertises read_only=true, job_execution=not_supported and gateway_reachable=false. An earlier independent remote SSH/HTTPS verification was explicitly refused by the security tool and is not retried via another channel. Hence the new script is NOT installed on Hostinger, no cron has been changed and actual Forgejo HTTP 200 / mirror freshness remains UNVERIFIED. The original AOI #7 and AOI-01 remain PARTIAL pending authorized Hostinger service management. Do not claim the synthetic process proof as real daemon recovery.
