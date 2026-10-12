# Lease — X Microcut 512Mi memory isolation
STATUS: RUNNING
AREA: x-microcut
DATE: 2026-10-12
RUN: none
JOB: none
COMMIT: f95a818f4f414fc79d699c07dccb3f65cf41f96a
SUPERSEDES: none
OWNER: anthares-crosschat-coordinator
LEASE_EXPIRES_UTC: 2026-10-12T13:50:00Z
TARGET_BRANCH: fix/microcut-semantic-x-e2e-20261011
BASELINE_PROVEN: Render service srv-db659q3bc2fs73artvfg deploy dep-db65fkd9fdbs73eskcs0 live; 512Mi OOM events at 10:10:33Z, 11:09:22Z, 12:06:55Z; branch f95a818f.
FAILED_AVOIDED: prior unbounded FFmpeg/Whisper execution OOM; no rerun of the unchanged pipeline or public posting.
SUCCESS_SIGNAL: isolated ASR child exits before FFmpeg, unit tests pass; actual free 512Mi deploy health ready=true without OOM is separately required.
FAILURE_SIGNAL: child ASR error, malformed timestamps, FFmpeg failure, or another Render OOM.
TEST_VALIDITY: static/mocked tests are labeled LOCAL_ONLY and cannot prove live 512Mi success; fail closed if source SHA or lease changes.

## Objetivo
Prepare an isolated, reviewable branch patch for ASR lifetime and FFmpeg thread bounds; preserve production control plane v16, other agent branches and all user sessions.

## Evidence
https://dashboard.render.com/web/srv-db659q3bc2fs73artvfg
https://github.com/UniversoAnthares/anthares-kwai-runner/commit/f95a818f4f414fc79d699c07dccb3f65cf41f96a

## Coordination
Read test-hub/README.md and AGENTS.md; GitHub findings index (743 entries) contains no unexpired x-microcut lease, and GitHub feature branch has no active workflow runs as of 2026-10-12T13:23Z. GitLab lacks this feature branch; no mirroring is authorized. The claim expires in 27 minutes. No deploy or live posting is authorized by this record.
