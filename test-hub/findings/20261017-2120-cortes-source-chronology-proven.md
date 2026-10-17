# CORTES source chronology cause confirmed and pending cycle repaired
STATUS: PROVEN
AREA: queue, wordpress-deploy
DATE: 2026-10-17
COMMITS: anthares-clipper 5995dd5da0636775246d04a0137fa781b3e07e2c; anthares-wordpress a263e2cfb9f783c8253ef73de2db3d4032ed6900
SUPERSEDES: test-hub/findings/20261017-2117-lease-cortes-source-chronology.md
LEASE: CLOSED

## Cause, not hypothesis
Read live WordPress registry and persisted source cycle. Registry has 154 lives, EVERY published_at empty, chronological_index 1..154. Initial migration intentionally marks 1..137 legacy-completed; first pending is #138 SJej0kuqELk (In the Name of Gath! - Reviewing your short stories LIVE!).
Python live_rows_from_state sorts correctly by chronological_index, but canonical ordered_lives re-sorted by (published_at, YouTube ID). With all dates empty, this becomes alphabetical video-ID order. Persisted 17-live pending cycle exactly matches that alphabetical order, beginning 1nJlreUmWKg (#144). This is why that source was picked. Its 11th-newest position alone was not sufficient diagnosis.
The claim that this initial migration should restart at the channel first live ignored the existing 137-live completed legacy cutoff. Do not erase that history.
At inspection current #144 was already completed, with three clips, long analyzed, short analyzed count0, and files_deleted_at 2026-10-17T20:58:31+00:00. No extra production round requested by owner.

## Fix
Canonical ordering prefers complete unique positive chronological_index. Dates only fallback when all present. Unknown chronology fails closed rather than sorting IDs. Regular-video discovery now persists the channel chronological index, preventing the same fallback bug there.
Migrate only the unconsumed source-cycle suffix, preserving completed prefix and held daily source. Never replace unfinished lock at midnight. Completed current-day source is not swapped for a second source that day.
WordPress validates ascending pending indices, lock/cursor consistency, no omitted pending lives or skipped cursor/history, finalized prior source and intentional cycle generation before accepting writes. GET supplies state SHA header; POST requires matching expected_state_sha256 inside flock mutex, rejecting stale writes.

## Live repair evidence
Backed up raw complete option in private maintenance directory; repair required serialized baseline SHA 3e72ad83211485e289b5c757b3c97361ab41295d927b6e74c05b65d7bb87e298. Preserved full daily_lock and all registry/clip data. Reordered 16 pending IDs only; did not reset current source, completed flags or legacy cutoff.
Final persisted SHA 37f4002132119e4373342931874856d4d5325039274597ed230c1f6e20c217c0.
Next pending: #138 SJej0kuqELk, #139 2lC3XP0gG9o, #140 ELbk0n7WsXA.
Final read policy=channel-chronological-index-v2, held=1nJlreUmWKg, next_pending=SJej0kuqELk, guard empty, legacy_cutoff=137.
Atomic isolated WordPress source-adapter deployment SHA256 939efc3f7f44763c9e7431990e440e6069537e9c66e584f33595bd82c2f51a0d from baseline 139af47218237fe6156aae6de6f3a462a5a62bd2ad60510eed9f02434723b20c, confirmed live matched original repository before change.

## Validation and limits
PHP lint PASS, 10 isolated PHP guard checks PASS, 38 focused Python regressions PASS, syntax/diff checks PASS. No production E2E, downloads, media rendering, new publication or workflow dispatch performed, as owner requested. GitLab target adapter/policy files absent at the checked older peer heads; no force push or blind mirror. This proves chronology repair and persisted pending order, not a newly executed full production round.
