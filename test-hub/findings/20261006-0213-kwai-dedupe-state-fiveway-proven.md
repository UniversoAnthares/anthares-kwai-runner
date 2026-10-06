# Kwai dedupe/state five-way acceptance proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37403019177
COMMIT: 1f6b7c584271f9936e7ee57bd4c54ffbbced287b
SUPERSEDES: test-hub/findings/20261006-0208-lease-kwai-dedupe-state-fiveway.md
LEASE_AREA: kwai-qa-dedupe
LEASE_CLOSED: 2026-10-06T02:13:10Z

## Five parallel acceptance probes
1. touching intervals are not false-positive overlap (end == next start is allowed).
2. contained interval is overlap and is rejected.
3. identical timestamps on a different source_id are not conflated.
4. failed terminal jobs are excluded from active dedupe while non-failed/UNCERTAIN remain protected.
5. canonical source_id/source_start/source_end fail-closed gate is present and current workflow has no ungated publisher path.

## Additional progress
During the first matrix, the canonical workflow assertion exposed that the current kwai-real-publish workflow had been reduced to queue self-test + guard and no longer carried the historical queued-job gate. Commit 2dc4b64648479921bb7faf44423d2439d9d12606 restored an explicit canonical interval fail-closed contract before any future real-publisher promotion. The initial fifth assertion expecting kwai_publish.sh in that guarded workflow was HARNESS_INVALID; corrected acceptance run is fully green.

## Consequence
CHAT 2 item 5 dedupe invariants are closed at code/acceptance level. A future real publisher promotion must preserve the canonical interval gate; no real publication is enabled by this change.
