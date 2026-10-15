# Fixed list items 9–11 — CLOSED — 2026-10-15

STATUS: PROVEN
AREA: canonical media model / central queue / dedupe
DATE: 2026-10-15

## Mandatory context rule
Before the next fixed-list item, first consult the latest state of the chat `Continuar resolução pendências` and current `main`. Parallel agents have changed this area during the same round; do not continue from a stale checklist snapshot.

## Item 9 — Source → Clip → Publication — CLOSED
- Canonical pure domain model: `anthares_publisher/media_model.py`.
- Stable identities and payload carry source ID, interval, content SHA-256/master identity, platform, account, target key and dedupe key.
- The model is deliberately persistence-free. It MUST NOT become a second operational queue/store.
- Source retention rule: source bytes are deletable only after processing is complete and all planned publications are confirmed.

## Item 10 — queue recovery & parallelism — CLOSED
- Existing Cloudflare control-plane fencing/recovery remains authoritative and already has proven lease-generation, stale-holder, pre-fence recovery and post-fence UNCERTAIN semantics.
- Publisher target v17 adds account-aware target scope to the central jobs model and leasing path.
- Same `(platform, account_id)` is serialized; independent accounts on the same platform are allowed to progress independently.
- Do not replace these semantics with local SQLite queue state.

## Item 11 — global dedupe ledger — CLOSED
- Central control plane remains the sole dedupe/reconciliation authority.
- Publisher target v17 scopes dedupe key, media SHA and source-interval overlap to `(platform, account_id)` instead of the entire platform.
- An UNCERTAIN post-fence outcome remains non-retriable until explicit reconciliation proves confirmation/absence; never republish merely because a worker disappeared.
- Local experimental queue/dedupe modules were removed so no competing authority survives.

## Verification
- `Publisher model QA` run `38685766108`: success; compile, central v17 patch validation and Source/Clip/Publication QA all passed.
- `Cloudflare Central Deploy Public Runner` run `38685747548`: success; canonical target migration applied, deploy snapshot validated, exact controller deployed, public health verified.
- Deployed line is publisher-target v17 (`2026-10-15-publisher-target-v17`).

## Architectural decisions for following agents
1. Cloudflare central control plane is the ONLY operational authority for enqueue, lease/renew, publication_started fence, dedupe, UNCERTAIN and reconciliation.
2. `anthares_publisher/media_model.py` is the domain contract feeding that authority, not another database.
3. `target_key = platform:account_id` is the concurrency/dedupe isolation boundary.
4. Preserve existing exactly-once publication rules proven by TikTok item 7; no retries after an ambiguous irreversible boundary.
5. Permanently retired: TinyFish, Browserless, WinRemote, MeshCentral, Render, CircleCI. Codespaces is retired from TikTok/Kwai social routes. Migrate residual functions instead of reviving these systems.
6. Before item 12, re-read `Continuar resolução pendências`, inspect latest `main`, and regression-check items 1–11. Adapt item 12 if newer acquisition work makes its original wording stale.
