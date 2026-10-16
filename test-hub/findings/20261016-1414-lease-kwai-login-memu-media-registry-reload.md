# Lease — Kwai login / MEmu media-registry reload
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-16
RUN: none
JOB: Anthares Remote
COMMIT: pending
SUPERSEDES: 20261016-1346-lease-kwai-login-memu-adb-single-daemon-repair.md
LEASE_OWNER: chatgpt-memu-media-registry-20261016-1414Z
LEASE_EXPIRES_UTC: 2026-10-16T14:44:00Z

BASELINE_PROVEN: Anthares Remote is healthy after the live timeout-tree fix. MEmu_4 can start headless and exposes 127.0.0.1:21543, but ADB remains offline. The VM log repeatedly reports `VD#0 ... VERR_ACCESS_DENIED` / `AHCI#0P0 ... VERR_ACCESS_DENIED`.

CAUSAL_EVIDENCE: `MEmuManage showhdinfo` reports the MEmu_4 disk2 medium as inaccessible because its file carries UUID `{20261016-cccc-cccc-cccc-000000000004}` while the active MEmu media object still expects `{20261015-cccc-cccc-cccc-000000000004}`. The current machine config now references the 20261016 UUID, while earlier pre-storage backups reference the 20261015 UUID. The SYSTEM MEmu service remained alive across those storage edits, so stale in-memory media registration is the least-destructive hypothesis to test before touching the 6 GB user disk.

ACTION: stop only MEmu_4 cleanly, restart MEmuSVC so it reloads current on-disk configuration/media metadata, then start MEmu_4 headless and test ADB. Do not change the disk header, copy/delete disk2, clear Kwai data, or publish.

SUCCESS_SIGNAL: `showhdinfo` no longer reports UUID mismatch/inaccessible; MEmu_4 reaches a stable running state; `adb -s 127.0.0.1:21543 get-state` returns `device`; then read-only F17 session probes may proceed.

FAILURE_SIGNAL: UUID mismatch persists after service reload, disk write errors continue, or VM fails to boot. In that case stop mutations and reconcile machine config/media UUID history before any header rewrite.

SAFETY: preserve MEmu_4 disk2 and Kwai session; no PC reboot; no publication; no clone operation.