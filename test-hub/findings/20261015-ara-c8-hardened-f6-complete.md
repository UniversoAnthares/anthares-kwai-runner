# ARA C8 hardened + F6 failover proof — 2026-10-15

## Canonical runtime

- Device: `DESKTOP-FTDK0HP`
- Identity/session: `SYSTEM`, Session 0
- Binary: `C:\ProgramData\AntharesRemoteAgent\anthares-remote-agent-v4-c8.exe`
- SHA-256: `3B8D68A15D56A907D0CE9A1E3E3A15DFF99699FB7F7C306E622FF4117DF06A8B`
- Source hardening commit: `870ec5d7bc58018c400337e8e8f6ac030923cc8e`
- Source queue blob: `175cf9938ff889ae7b2f6154c647a7739eeb63f4`
- `ANTHARES_MAX_CONCURRENT=8`
- GitHub private issue queue: enabled
- GitLab private issue queue: enabled
- Recovery watchdog: enabled
- Interactive/user fallback: disabled

## Queue starvation fixes

The canonical issue-queue implementation now:

1. polls GitHub and GitLab independently, so a slow provider does not block the other;
2. keeps polling while long-running jobs execute;
3. uses a persistent in-flight map keyed by `job_id` to prevent same-process cross-provider races;
4. uses bounded workers;
5. paginates both providers with `per_page=100` and pages `1..20`, removing the former first-30 starvation condition.

The finalizer was updated in commit `0a601fab5289814108e9385cbc57bb8665586444`. GitHub Actions run `38678881042` passed validation and finalized the source. An independent Windows `go test ./...` and Windows/amd64 build also passed before deployment.

## Live non-blocking proof

GitHub queue job `ara-hardened-long2-20261015-0404` started at `2026-10-15T04:04:33Z` and remained running until `04:05:54Z`.

While that job was still in state `started`, job `ara-hardened-fast-during-long-20261015-0404` was discovered, executed, and returned `pong` at `04:05:14Z`. Therefore polling/discovery is no longer blocked by completion of the current batch.

## Live failover proof

### GitHub unavailable / GitLab only

The canonical runtime was restarted with GitHub queue configuration deliberately disabled while GitLab remained enabled. Supervisor state confirmed `github_queue=false`, `gitlab_queue=true`.

GitLab issue `#6`, job `ara-f6-gitlab-only-20261015-0409`, executed exactly once and returned `pong` with provider `gitlab`.

### GitLab unavailable / GitHub only

The canonical runtime was then restarted with GitLab queue configuration deliberately disabled while GitHub remained enabled. Supervisor state confirmed `github_queue=true`, `gitlab_queue=false`.

GitHub issue `#132`, job `ara-f6-github-only-20261015-0410`, executed exactly once and returned `pong` with provider `github`.

The original dual-provider configuration was restored afterwards and verified as `github_queue=true`, `gitlab_queue=true`, `dual_queue_redundancy=true`.

Cross-provider same-`job_id` deduplication had already been proven by GitHub issue `#114` and GitLab issue `#4`, which shared one persisted receipt/result and did not execute twice.

## Recovery proof after hardened deployment

- Killing the canonical C8 agent caused the SYSTEM supervisor to launch a new agent automatically; post-recovery count returned to exactly one.
- Stopping the canonical SYSTEM supervisor task caused the recovery watchdog to restart the canonical task. The watchdog state returned `single-writer-healthy`, `system_v4_count=1`, GitHub=true, GitLab=true.
- No reboot was performed.

## Final state

At cleanup:

- `Anthares Remote Agent SYSTEM`: Running
- `Anthares Remote Recovery Watchdog`: Running
- exactly one C8 agent in Session 0
- GitHub + GitLab queues both enabled
- dual queue redundancy enabled
- no interactive agent
- temporary failover/deployment/fault-test scheduled tasks removed
- temporary failover credential backup removed

F6 can be considered `PASSED` for bidirectional transport failover plus cross-provider deduplication. F15 reboot remains intentionally untested pending explicit authorization.