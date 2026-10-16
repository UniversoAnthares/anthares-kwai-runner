# Lease — Anthares Remote timeout-tree liveness fix deploy
STATUS: RUNNING
AREA: queue
DATE: 2026-10-16
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38911651024
JOB: Anthares Remote
COMMIT: 6d8c1d115534fd2ece9ad07de7a5f05304eb015a
SUPERSEDES: none
LEASE_OWNER: chatgpt-ara-timeout-tree-20261016-1357Z
LEASE_EXPIRES_UTC: 2026-10-16T14:27:00Z

BASELINE_PROVEN: Vercel+Neon Anthares Remote returned a fresh command roundtrip at 2026-10-16T13:56:46Z. Earlier in this same round, a `memuc.exe` shell job left a stale leased job and temporarily stopped job consumption while heartbeat remained fresh. The queue later recovered automatically.

FAILED_AVOIDED: Do not rely on heartbeat alone as execution health. The source fix in commit 5812220b2cfc84161b69c79c5657dab6b833f237 changes Windows command cancellation from direct-child termination to full process-tree termination plus bounded WaitDelay. Stale publish-workflow guards were aligned to current Vercel+Neon primary in commit 6d8c1d115534fd2ece9ad07de7a5f05304eb015a.

SUCCESS_SIGNAL: canonical C8 binary is deployed through the existing SYSTEM deployment path; exactly one SYSTEM agent remains; fresh ping/short command succeeds; a controlled child-process timeout returns within a bounded interval and subsequent ping succeeds without queue buildup.

FAILURE_SIGNAL: deploy breaks the canonical agent, creates multiple writers, or controlled timeout again leaves the queue unable to consume jobs.

TEST_VALIDITY: GitHub run 38911651024 must be successful and publish the validated release asset before live deployment. Existing queue/HTTP recovery architecture must remain Vercel+Neon primary with GitLab/GitHub private queue recovery.

SAFETY: no PC reboot. Preserve credentials, device identity, queue state and MEmu/Kwai data.