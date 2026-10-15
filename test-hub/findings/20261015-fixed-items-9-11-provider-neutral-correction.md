# Fixed list items 9–11 — provider-neutral correction — 2026-10-15

STATUS: PROVEN
AREA: canonical media model / queue semantics / global dedupe
DATE: 2026-10-15
SUPERSEDES: `test-hub/findings/20261015-fixed-items-9-11-closed.md` where it called Cloudflare the sole/mandatory authority

## Mandatory context rule for every next agent
Before **each architectural decision**, consult deeply the latest state of both chats named exactly:
1. `Continuar resolução pendências`
2. `SISTEMA DE UPLOADS`

Then inspect current `main` and adapt stale decisions. Do not continue only from an old handoff/checklist.

## Correction that matters
The user explicitly requires that **Cloudflare, or any single provider, must not become mandatory canonical authority**. Therefore:
- `anthares_publisher/media_model.py` is provider-neutral and persistence-free.
- Stable `Source -> Clip -> Publication` identity survives backend/failover changes.
- Cloudflare `anthares-control` v17 is the **current primary queue implementation**, not the domain/canonical authority.
- Production WordPress Distributor 0.4.0 is an independent durable delivery ledger/witness already PROVEN with `destination_key`, `lease_generation`, `publication_started_at`, `remote_id`/finish evidence and `confirmation_evidence`; see `20261006-0850-distributor-multichannel-destination-key-proven.md`.
- A provider outage must never authorize blind replay. Stable publication IDs/dedupe keys plus durable delivery evidence are the invariant across transports.

## Item 9 — Source → Clip → Publication — CLOSED
Provider-neutral pure domain model is implemented in `anthares_publisher/media_model.py`:
- stable source/clip/publication identity;
- short master 30–90 s; long master 5–14 min;
- platform/account isolated `target_key`;
- portable control payload with `master_id`, content SHA-256, source interval and dedupe key;
- source retention only after processing complete + all planned publications confirmed.

## Item 10 — queue recovery & parallelism — CLOSED at semantic/backend level
- Existing v16 fencing/recovery proof remains valid: TTL/heartbeat, `lease_generation`, stale-holder rejection, pre-fence recovery, post-fence `UNCERTAIN`.
- Cloudflare publisher-target v17 adds `(platform, account_id)` isolation and per-account quota/fairness to the current primary queue backend.
- WordPress Distributor 0.4.0 independently persists destination-scoped lease/fence/completion evidence; therefore canonical delivery safety is not defined only by Cloudflare state.
- Same target serializes; distinct authorized accounts remain independent.

Important scope boundary: **cross-provider automatic queue failover/failback is a separate infrastructure concern and must not be falsely marked proven here**. Historical GitHub/GitLab transport work does not yet prove once-only cross-provider failover/receipt/antireplay. Do not infer that it does.

## Item 11 — global dedupe/reconciliation — CLOSED at canonical semantics level
- Dedupe identity is stable across providers: master/content hash + source interval + `(platform, account_id)`.
- Current Cloudflare v17 applies key/hash/temporal-overlap dedupe per target.
- Durable delivery ledger retains destination-scoped publication fence and confirmation evidence independently of the queue implementation.
- Any ambiguous post-submit outcome remains `UNCERTAIN`; no retry until reconciliation proves published/confirmed or proves absence.
- Local experimental SQLite queue/dedupe authorities were removed; do not recreate a competing canonical store.

## Verification already passed
- `Publisher model QA` run `38685766108`: SUCCESS.
- `Cloudflare Central Deploy Public Runner` run `38685747548`: SUCCESS, deployed `2026-10-15-publisher-target-v17` and verified public health.
- Independent pre-existing delivery-ledger proof: `test-hub/findings/20261006-0850-distributor-multichannel-destination-key-proven.md`, STATUS PROVEN.

## Next-agent invariants
- Only Anthares Remote for remote administration; Anthares Browser for browser work.
- PC is not the normal media/publication executor.
- TinyFish, Browserless, WinRemote, MeshCentral, Render and CircleCI remain retired/unavailable per latest decisions; do not revive them as shortcuts.
- Do not reboot the PC for configuration/environment refresh. Restart/reload only the affected component/service and prove the postcondition. Full reboot is reserved for an explicit boot-persistence test or a demonstrated Windows limitation, and requires the appropriate user authorization when applicable.
- Never let provider loss convert `publication_started`/ambiguous state into retry-safe.
- Before proceeding to item 12 or any later architectural choice, re-read BOTH required chats and current `main`.
