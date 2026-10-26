STATUS: PARTIAL
OWNER: chatgpt-ops / ISO08-20261026
DATE_UTC: 2026-10-26
TARGET: CORTES-ISO-08 (fixed 14), account threads:universoanthares

## Governance / preflight
GitHub governance main manifest version 2e28d54043d6bad1; local Windows manifest f6fc9ca59a96e451. `policy.py preflight` PASS for D:\AntharesWork\anthares-clipper. Preserve version divergence; no blind sync. Read current AGENTS.md and Test Hub README; lease reserved separately in this draft PR.

## QA implementation
Anthares-clipper branch platform/iso08-qa-rehearsal-20261025, PR https://github.com/UniversoAnthares/anthares-clipper/pull/207 (DRAFT).
Old workflow had broken PowerShell regex and duplicated tail following previous textual update. Root cause of attempted patch: JS replace interpreting replacement text `$'` as post-match injection. Repaired from pristine current main source using replacement callback (literal $ preserved).
Fix commit 729de5c87b3bbab52d76dda9e0e86c5fda76fe6e; workflow blob b4a4c999ed69dd76f2bad7004b25dd637cfb6511. Fresh readback: exactly one upload-artifact step, unbroken regex, >=30-case check. Test file contains 30 tests, three newly added. Production flags remain `cutover_authorized=false`, `deploy_authorized=false`.
GitHub Actions run 40318736802 / job 121557877097 triggered via normal PR CI: `in_progress` in last observation; no SUCCESS/FAIL claimed yet. Additional `CORTES - 40 YouTube Shorts Daily` PR validation run 40318736821 queued, validation-only job observed.

## Live read-only facts
Neon production project purple-flower-35918989 / branch br-crimson-unit-b89nau08 / table public.cortes_publications: target Threads 130 confirmed, 163 queued, 2 failed; 0 active leases and 0 leased/started/uncertain at instant read. Handoff owner=local, epoch 57, cloud_primary_enabled=false, lease_until NULL; previous confirmed URL historical, not new canary.
RLS disabled, FORCE disabled; no row-level access policies. cloud_admin, neon_service, neondb_owner have BYPASSRLS. Two enabled cross-network Kwai fanout triggers remain active.
All 163 queued payloads have media_sha256, but zero have transcript_sha256 or editorial_attestation there; media_sha256 in dispatch does not independently prove bytes. Editorial proof registry on runner/main blob 9cda87c0ce8753f1a9cc0b4d15b4c236b53576b8 holds one attested entry; compared IDs without printing: matches one already confirmed post, no queued or failed entry.
No real platform verification of a new post, new editorial canary, external rollback, or per-account credentials proven.

## Change boundary and rollback
No modifications to live publishers, SQL, queues, identities, ACL, scheduler, secrets, social platform or primaries; no cutover, no canary. Discard PR#207 to rollback code proposal. Previous security refusal for Windows temp sandbox was not bypassed. Normal PR CI is a separate existing review workflow, not reissuing that blocked remote directory operation.
ISO-08 status: PENDENTE. Do not mark complete without per-account identity, editorial candidate, ISO-07 live canary, single-writer and rollback receipts.
