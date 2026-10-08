# Shared test-hub protocol

Before ANY change or test in this project, the agent MUST perform the hub preflight below. Reading only README is not sufficient.

## Mandatory preflight
1. Read `test-hub/README.md`.
2. List `test-hub/findings/` and read ALL findings newer than the last consolidated timestamp in README for the same area/causal chain, plus every finding explicitly referenced by them through SUPERSEDES/baseline.
3. Check current GitHub Actions/GitLab runs for the same causal chain. Do not launch a competing experiment while a causally relevant RUNNING test exists, unless the new test is explicitly an independent layer.
4. Before creating a run, write its RUNNING finding first (or in the same change set) with:
   - BASELINE_PROVEN
   - FAILED_AVOIDED
   - SUCCESS_SIGNAL
   - FAILURE_SIGNAL
   - TEST_VALIDITY
5. A matrix may branch only AFTER every variant reaches the same observable precondition. If a job does not reach that precondition, classify it INVALID/NOT_TESTED, never as hypothesis FAILED.
6. A green job is not PROVEN unless its declared SUCCESS_SIGNAL appears in evidence.
7. After completion, append a new finding and SUPERSEDE the RUNNING finding. Update README consolidated state when the causal conclusion changes.

## Mandatory read-before-write gate
Every mutation, including documentation and CI changes, MUST follow this sequence on every round:
1. Read the complete current target file from the provider that will receive the write. For a new file, read the destination directory/tree and current branch HEAD.
2. Record the current branch HEAD and the target blob/file SHA or last commit ID.
3. Read/check the peer provider for the same ref/path before reconciling or mirroring. Never assume same filename means same content.
4. Acquire/verify the active Test Hub lease for the mutation area.
5. Prepare a minimal patch from the content actually read in this round.
6. Immediately before writing, re-read the destination HEAD. If it changed, ABORT the write, re-read the target and rebuild the patch.
7. Use optimistic concurrency: GitHub writes must supply the current blob SHA; GitLab writes must supply `last_commit_id`/equivalent expected base. A stale-base rejection is a safety success, not an error to bypass.
8. Never force-push, reset a shared branch, or perform blind mirroring. If histories diverge, preserve both histories. If trees are equivalent, converge with a normal two-parent merge or use content-equivalence-aware failover. If trees differ, reconcile each differing file explicitly and rerun validation.
9. No production/live publication may be used merely as a code audit probe.
10. After a mutation, rerun the relevant syntax/unit/CI checks and append evidence to the Test Hub.

## Dual-provider safety
- GitHub and GitLab are execution peers, but commit IDs can legitimately differ after independent provider history. Cross-provider failover must use an explicit verified content identifier (for example the Git tree SHA) when commit IDs differ.
- A lease on one provider remains fenced to the exact HEAD acquired; content-equivalent movement on that same provider is still a concurrent write and must abort/re-read.
- Provider failover is permitted only after the active provider is not READY and the target provider is READY with equivalent verified content.
- Direct pushes to protected branches should be disabled where the hosting plan supports it. Where native branch protection is unavailable, the read-before-write/lease/optimistic-concurrency gate remains mandatory and production automation must not bypass it.

## Preservation rules
- Treat the hub as the shared source of truth across simultaneous chats/agents.
- Do not repeat a FAILED path unless the new test explicitly changes the recorded failure cause.
- Preserve PROVEN behavior unless newer real evidence supersedes it.
- Never put credentials, secrets, cookies, tokens, or session payloads in the hub.
- Harness failure is not evidence that the tested hypothesis failed.
- Do not infer success/failure from workflow conclusion alone; inspect decisive logs/artifacts.
