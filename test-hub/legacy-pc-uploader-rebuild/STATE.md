# LEGACY PC UPLOADER STATE

Status values: UNKNOWN / FOUND / RESTORED / PROVEN / FAILED / BLOCKED

## TikTok
Executor: FOUND — historical local source family and repository recovered; exact production self-hosted workflow still to identify
Session: UNKNOWN
Queue: UNKNOWN
Ledger: FOUND — historical repository contains TikTok ledger/pipeline artifacts; exact production state file still to map
Upload page: FOUND — local TikTok web publisher family recovered on PC
Publish: UNKNOWN — exact production entrypoint/version still to select
Confirmation: UNKNOWN
Last proven real post: HISTORICAL PROVEN — @universo.anthares, historical ID 7692917905595370770
Current blocker: identify exact self-hosted workflow, browser profile/session path, and production publisher version in UniversoAnthares/anthares-clipper

## Kwai
MEmu: FOUND — exact publisher/recovery code recovered
ADB: FOUND — exact publisher/recovery code recovered
Kwai package: FOUND — com.kwai.video in recovered source
Authenticated account: UNKNOWN — runtime account must be verified before E2E
MediaStore: FOUND — exact staging/query/cleanup implementation recovered
Album: FOUND — exact long-press/stable Album/Videos flow recovered
Editor: FOUND — exact editor navigation logic recovered
ShareActivity: FOUND — exact activity/resource-id validation recovered
Publish button: FOUND — com.kwai.video.basis:id/post
Confirmation: FOUND — recovered publisher includes 120-second structural/textual/profile evidence gate
Daemon: FOUND — C:\Users\Lucas\anthares-clipper\kwai_daily_daemon.py, SHA-256 14B31D4BFE50B6B0B3103B08DAAB693132A9E7926C4EB12DD1BA6F403C088527
Scheduled Task: UNKNOWN — legacy daemon task absent from current task list; exact launcher still to recover
Last proven real post: HISTORICAL PROVEN — up to 31 confirmed publications / next_index=32
Current blocker: map last proven commit/runtime configuration, recover exact daemon Scheduled Task, verify current VM/account/runtime before E2E

## Shared
Queue: FOUND — recovered daemon contains central enqueue/lease/complete/fail integration
Lease: FOUND — recovered daemon contains central lease handling
Dedupe: FOUND — mature recovered daemon has persistent source+interval reservation and no wrap-around
Timeline ledger: FOUND — source-segment-history.json implementation recovered
Source selection: FOUND — live-media metadata + source-history selection recovered
Logging: RESTORED

## Archaeology
Historical primary repository: FOUND — UniversoAnthares/anthares-clipper
PC primary copy: FOUND — C:\Users\Lucas\anthares-clipper
PC cloud copy: FOUND — C:\Users\Lucas\AntharesWork\anthares-clipper-cloud
GitLab mirrors: FOUND — later mirrors only
PC archaeology: FOUND via MeshCentral; AI Commander remains temporarily gated
Exact legacy daemon source: FOUND
Exact kwai_memu_publish.py source: FOUND — version 0.2.2, SHA-256 5257623F994BE9B2B12B4FED9DC1996616784004AF4A490E41B88FD2F36650B0
Historical commit 33c1596: FOUND in local anthares-clipper history
Historical commit 106dff4: FOUND in local anthares-clipper history
Historical commit hint 253be4b3: still UNKNOWN/possibly earlier rewritten or different ref; lower priority now that exact files/history are recovered

## Coordination
Canonical path: test-hub/legacy-pc-uploader-rebuild/
SHARED-LOG.md: RESTORED
STATE.md: RESTORED
Agent 3 last sync: 2026-10-12 14:22 -04:00
