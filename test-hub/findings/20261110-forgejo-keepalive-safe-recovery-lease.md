# AOI #7 / AOI-01 — isolating Forgejo keepalive safety repair
STATUS: RUNNING
AREA: architecture/forgejo-daemon-hostinger-keepalive
OWNER: chatgpt-forgejo-keepalive-20261110
DATE_UTC: 2026-11-11
BRANCH: fix/forgejo-keepalive-safe-recovery-20261110
BASE_SHA: 9075b960b7a10cb3d8ba41367c7d6288a6c20e45
GOVERNANCE_SHA: 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
KEEPALIVE_BASE_BLOB: 0170eb85c15e1ab8a882e08be0ee68e460632bd6
PEER: GitLab 87307248 stores the same historical keepalive implementation; histories intentionally independent.
BASELINE: Hostinger ARA read-only (job_execution=not_supported); gateway_reachable=false; last operator-only Forgejo recovery 2026-11-09 reached healthy UNIX socket but HTTPS verification was blocked; service later reported 502.
FAULT: current keepalive removes socket after one failed HTTP probe without verifying live Forgejo process; flock contention exits success with no signal.
SCOPE: amend only the GitHub keepalive script + isolated offline test, no Hostinger runtime administration, no cron changes, no daemon start, no publishing, no source or mirror resets.
SAFETY: do not use alternate channel to bypass security refusal of earlier Hostinger SSH/HTTPS verification. Remote runtime deployment remains separate; source changes do not imply installation.
ACCEPTANCE: fail closed for live unhealthy process or non-socket occupant, lock contention signals failure, healthy returns without mutation, stale socket recovery starts at most one daemon; synthetic tests pass.
