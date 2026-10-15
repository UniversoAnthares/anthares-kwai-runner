# Fixed list items 12–14 — acceptance/handoff — 2026-10-15

STATUS: CURRENT
AREA: acquisition / semantic clipping / Kwai remote publisher
DATE: 2026-10-15

## Mandatory cross-chat rule
Before the next fixed-list decision, deeply review the latest state of both chats `SISTEMA DE UPLOADS` and `Continuar resolução pendências`, then inspect current repository state and regression-check previously closed phases. Do not continue from this file alone if either chat has newer evidence.

## Architecture correction carried forward
- The publication/control contract is provider-neutral.
- Cloudflare is the current primary control backend, not a conceptual permanent authority lock.
- Preserve a durable provider-independent delivery/evidence witness during future backend migrations.
- Permanently retired: TinyFish, Browserless, WinRemote, MeshCentral, Render, CircleCI. Codespaces is retired from TikTok/Kwai social routes.
- Anthares Remote is the only remote-control surface; Anthares Browser is the only browser-automation surface.
- PC/MEmu is not the normal social publication executor unless a later explicit architecture decision changes that rule.

## Regression review before 12–14
- Public control health: `publisher-target-v17`, persistent state true, queue bound true, PC fallback false.
- Anthares Remote stayed connected with zero queued/leased jobs. Two `uncertain` Remote jobs are administrative, not publication jobs: one historical BlueStacks installer help job from 2026-10-13 and one private-Git administrative fetch attempt from this round. Do not confuse them with publication `UNCERTAIN` in the delivery ledger.
- Fresh private-repository schedules in `anthares-clipper` failed before executing any workflow step (`runner_id=0` / no steps). Classify as private Actions infrastructure/quota, not clipping-code regression.

## Item 12 — normalized acquisition — ACCEPTED/CLOSED
Current `anthares-clipper/youtube_tiktok_pipeline.py` acquisition order is:
1. validated/current source cache by source video ID; cache hit is hardlinked or copied into work area and returns before any network acquisition;
2. author-owned archive registry direct HTTP source, with video/audio/duration validation;
3. archive downloader fallback;
4. direct source downloader fallback;
5. successful acquisition is atomically persisted into the source cache for reuse.

Fresh independent invariant QA through Anthares Remote:
- `ITEM_12_ACQUISITION_CACHE_ACCEPTANCE=PASS`

Known hardening note, not a rollback of closure: current cache-hit branch assumes bytes written by the validated acquisition path and checks file size before reuse; a future integrity-manifest/SHA revalidation can harden against out-of-band cache corruption without changing the acquisition architecture.

## Item 13 — persistent semantic clipping/no repeated timecodes — ACCEPTED/CLOSED
Current pipeline behavior:
- semantic scoring uses interest, isolated clarity, density and title potential; AI candidates require all dimensions >= 7;
- administrative openings/filler are rejected;
- AI Hub is not a single point of failure: timestamp-based local segmentation fallback exists;
- candidate selection removes every timeline overlap, not merely exact duplicates;
- reanalysis checks new candidates against all persisted existing intervals and refuses overlap;
- `attempted` halts ambiguous continuation; `published` and `attempted` do not re-enter ready selection;
- short render requires semantic microcuts and the mandatory microcut pass before creative layout.

Fresh independent invariant QA through Anthares Remote:
- `ITEM_13_NO_OVERLAP_PERSISTENCE=PASS`
- `ITEM_13_ATTEMPTED_PUBLISHED_REUSE_BLOCKED=PASS`

## Item 14 — Kwai remote — CURRENT EXECUTOR AND MIGRATION
Current primary executor selected for this item is public GitHub-hosted Android/KVM, not the PC, via `.github/workflows/kwai-queue-publisher-v17.yml`.
Expected account is `lucasrosalem`.
The publisher uses the existing encrypted private Kwai session vault, exact UI/account identity probe, central lease/fence path, confirmed publication evidence and explicit UNCERTAIN reconciliation without blind republish.

Changes made in this round:
- `744d8ec5f70bef826cdae0d8dc572ea5f7798dd2` — added current public Android publisher for target-v17.
- `f2d046ef943dfcb16188b0c2d997108b28d367cc` — migrated vault-client preflight from obsolete v16 to target-v17.
- `e457fba4223532388f8a90202e886cc8acddf836` — authorized the v17 publisher workflow in the private Kwai session-vault OIDC allowlist.
- Cloudflare deploy run `38742482842` completed successfully after that authorization change; deploy snapshot, vault tests, exact deploy and public health all passed.
- Publisher run 1 `38741003030`: correctly stopped before Android because vault client still required v16.
- Publisher run 2 `38741176546`: correctly reached OIDC and stopped with 401 because the new workflow was not yet in the vault allowlist.
- Publisher run 3 `38742730475`: triggered after the allowlist deploy; inspect its final result before declaring the real-publish acceptance complete.

## Rules for the agent finishing item 14
1. Do not retry a publication if the v17 publisher crosses `publication_started` and becomes ambiguous. Reconcile first.
2. Require exact Kwai identity evidence for `lucasrosalem` before mutation.
3. If queue is empty, that is executor/session validation only, not a real-publication proof; enqueue one controlled deduped author-owned clip through the existing central/provider-neutral contract, then verify profile + remote ID/public URL + durable delivery evidence.
4. If the private vault contains no valid authenticated Kwai session and automated credential recovery cannot establish identity, stop at that irreducible account-auth boundary and give the user the smallest manual login step.
5. Do not promote MEmu/PC to production merely to bypass a remote-session failure.

## Before item 15
Re-read both continuity chats, inspect this run's final evidence, regression-check items 1–14, and adapt YouTube/Shorts acceptance if another agent has advanced it meanwhile.
