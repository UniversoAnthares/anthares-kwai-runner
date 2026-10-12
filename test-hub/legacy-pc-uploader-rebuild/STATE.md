# LEGACY PC UPLOADER STATE

Status values: UNKNOWN / FOUND / RESTORED / PROVEN / FAILED / BLOCKED

## TikTok
Executor: PROVEN — reconstructed local-PC controller executed a real publisher transaction successfully on 2026-10-12
Session: PROVEN — authenticated session works; actual posting identity from TikTok Studio is @lucasrosalem4. Earlier public-profile navigation to @universo.anthares did not establish login identity.
Queue: FOUND — historical queue/workflow family recovered; local ledger/plan path restored
Ledger: PROVEN for transaction semantics; corrected chronological-v3 ledger is staged separately so the rejected first test does not contaminate the new source-order cycle
Upload page: PROVEN — media attachment, caption and public visibility validated repeatedly
Publish transaction: PROVEN historically in reconstruction — real controlled Post succeeded for segment `xcRGdBfHX0E:100:190`
Confirmation: PROVEN — `TIKTOK_OWNED_PUBLISH=OK` followed by `LEGACY_TIKTOK_PUBLISH=CONFIRMED_AND_COMPLETED`
Last proven real post: @lucasrosalem4 — https://www.tiktok.com/@lucasrosalem4/video/7695869978876136705 — REJECTED AS EDIT QUALITY REFERENCE by user; do not reuse its layout/edit decisions
Safety after proof: PROVEN — one-shot ALLOW_PUBLISH removed; automatic publication remains disarmed

Corrected edit/source policy v3: RESTORED/STAGED on isolated branch `UniversoAnthares/anthares-clipper:legacy-pc-rebuild`
- Source order: complete `/streams` catalog oldest->newest, then complete `/videos` catalog oldest->newest, then cycle reset to the oldest live.
- YouTube-bound clipper remains live-only; normal videos were added only to the TikTok/Kwai-style owned short-source policy requested by user.
- Oldest expected live: `b6gL9plY_6w` — `A Poética de Aristóteles - Parte 1 (LIVE)`.
- Source records now persist `source_kind`, `catalog_index`, live/video boundary and total catalog size so later runs cannot lose ordering metadata.
- Catalog discovery no longer inherits the old 100/300-source clamp; v3 uses a dedicated full-catalog limit (default 5000).
- Microcuts are mandatory: safe repetition/silence edits + conversational pause cuts; render is rejected if no genuine internal edit removes at least 0.08s.
- Adaptive layout preserves the entire original source frame in every accepted composition; presenter crops are supplementary only, never replacements for the full context.
- Hard QA gate checks chronological metadata, live/video boundary, mandatory microcuts, adaptive layout/full-frame preservation, 1080x1920 output and duration before any publication.
- `publish()` re-runs QA immediately before the real Post click.

Current TikTok execution transport: replacement local transport CONSTRUCTED/STAGED via Anthares Local Executor v2. First queue round-trip is still pending proof. Legacy WinRemote/Desktop Commander/AI Commander are no longer architectural requirements after first successful supervisor heartbeat.
Identity blocker remains: before any next real publication, verify/choose the intended TikTok posting account because the recovered session is @lucasrosalem4 while prior target assumptions referenced @universo.anthares.
Continuous social scheduler remains OFF.

## Kwai
MEmu runtime: PROVEN/RESTORED — MEmu 9.5.7.1 installed at historical `D:\Program Files\Microvirt\MEmu` path
Historical VM index: RESTORED — VM3 exists, boots Android 9 x86_64 and exposes ADB
Kwai package: PROVEN INSTALLED — recovered validated split vault installed in VM3 as `com.kwai.video`, version 13.8.30.646601
APK integrity: PROVEN — all 11 vault APK hashes matched historical MANIFEST.tsv before install
Authenticated account: UNKNOWN — still must be restored/verified before E2E publication
Onboarding: PARTIAL/ADVANCED — interest flow advanced through 9/9 and completion action accepted; current path reached dynamic-module/tiny-web preparation gate and skip confirmation work
MediaStore: FOUND — exact staging/query/cleanup implementation recovered
Album: FOUND — exact long-press/stable Album/Videos flow recovered
Editor: FOUND — exact editor navigation logic recovered
ShareActivity: FOUND — exact activity/resource-id validation recovered
Publish button: FOUND — `com.kwai.video.basis:id/post`
Confirmation: FOUND — recovered publisher includes 120-second structural/textual/profile evidence gate
Daemon: FOUND — recovered mature local daemon
Scheduled Task: FOUND — historical task `Anthares-Kwai-Daily-Publisher`: pythonw.exe `D:\AntharesWork\anthares-clipper\kwai_daily_daemon.py`, AtLogOn, StartWhenAvailable, MultipleInstances IgnoreNew, Hidden
Last proven real post: HISTORICAL PROVEN — up to 31 confirmed publications / next_index=32
Current blocker: finish Kwai post-onboarding/login restoration, verify target account in VM3, then run safe probe/pre-publish and one controlled E2E

## Shared
Queue: FOUND — recovered historical daemon contains central enqueue/lease/complete/fail integration
Lease: FOUND — recovered daemon contains central lease handling
Dedupe: FOUND — mature recovered daemon has persistent source+interval reservation and no wrap-around
Timeline ledger: FOUND — source-segment-history.json implementation recovered
Source selection: FOUND — live-media metadata + source-history selection recovered
Logging: RESTORED

Anthares Local Executor replacement transport: RESTORED/STAGED
- Control plane: immutable GitHub JSON queue on isolated `anthares-clipper:legacy-pc-rebuild` branch.
- Executor: `anthares_local_executor_v2.py`, allowlist-only; no arbitrary shell command surface.
- Self-healing supervisor: `anthares_executor_supervisor.py`, heartbeat/PID monitoring every 20s.
- Persistence: verified Startup launcher at `C:\Users\Lucas\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Anthares-Local-Executor.cmd`.
- PC code paths staged: `D:\AntharesWork\anthares-pc-legacy\anthares_local_executor_v2.py` and `anthares_executor_supervisor.py`.
- Publish safety: publish actions require both queue `publish=true` and matching local guard file.
- Smoke request pending: `c9c9bf17-67e2-4c07-90f1-724933aa62c6` action=`status`; no result yet.
- Immediate MeshCentral launch outcome: UNKNOWN because command channel returned OK without observable heartbeat. Next Windows user logon will launch supervisor through Startup even if all three former executors remain unavailable.
- Status: architecture CONSTRUCTED; end-to-end GitHub queue round-trip not yet PROVEN.

## Archaeology
Historical primary repository: FOUND — UniversoAnthares/anthares-clipper
PC primary copy: FOUND — C:\Users\Lucas\anthares-clipper
PC cloud copy: FOUND — C:\Users\Lucas\AntharesWork\anthares-clipper-cloud
GitLab mirrors: FOUND — later mirrors only
PC archaeology: FOUND via MeshCentral; AI Commander remains temporarily gated by daily sign-in
Exact legacy daemon source: FOUND
Exact kwai_memu_publish.py source: FOUND — version 0.2.2, SHA-256 5257623F994BE9B2B12B4FED9DC1996616784004AF4A490E41B88FD2F36650B0
Original kwai_memu_publish.py commit: PROVEN — 253be4b3d13bffc1f9fed599beae40161b606579, version 0.1.0
Historical commit 33c1596: FOUND
Historical commit 106dff4: FOUND
Historical commit 7592779: FOUND — moved continuous Kwai publishing to local daemon
Historical commit 796a3a1: PROVEN — exact detached Scheduled Task launcher recovered
TikTok self-hosted historical window: FOUND — bounded before commit 21ffa81 cloud migration

## Coordination
Canonical path: `UniversoAnthares/anthares-kwai-runner/test-hub/legacy-pc-uploader-rebuild/`
SHARED-LOG.md: RESTORED/CANONICAL
STATE.md: UPDATED with TikTok v3 corrections, current Kwai runtime progress, and Anthares Local Executor replacement transport
Functional reconstruction branch: `UniversoAnthares/anthares-clipper:legacy-pc-rebuild`
Current rule: read canonical SHARED-LOG before any further investigation/change/test; append result after each step. Do not modify modern cloud systems for this reconstruction.
