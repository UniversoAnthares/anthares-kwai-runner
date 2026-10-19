# Authorized host storage cleanup and recurring maintenance
STATUS: PROVEN
AREA: storage, local-maintenance
DATE: 2026-10-18
RUN: local authorized cleanup; Windows scheduled task verification
SUPERSEDES: 20261017-host-cleanup-lease.md
LEASE: CLOSED

## Evidence
Fresh inventory and process checks preceded deletion. Local D: free space had fallen below 0.8 GiB. Exact-path allowlist, reparse-point protection, age rules, fresh size/time checks and exclusive read against active writers were enforced. No recursive directory removal.

Applied manifest: D:\AntharesWork\anthares-clipper\longs-audit\maintenance\cleanup-plan-20261018-212523.json.
Result: cleanup-result-20261018-212523.json in the same directory. Deleted 6857 files / 13530227346 bytes; skipped zero. C:1886 files/1507269629 bytes; D:4971 files/12022957717 bytes. Observed free space after cleanup C:10.34 GiB, D:11.90 GiB.

Only used installers/extracted archives, old corrupted artifact ZIPs, obsolete incomplete source from failed run39075764332, rebuildable browser/package caches and old diagnostics were removed. Browser optional AI model was initial-cleanup only. Runtime code, Git history, credentials, cookies/sessions, queues, installed tools, dependency models, session backups and pending masters preserved. No WordPress or Android media deletion.

Installed D:\AntharesWork\maintenance\Invoke-AntharesStorageMaintenance.ps1. Task Anthares Safe Storage Maintenance daily04:15, StartWhenAvailable, hidden, current interactive user without extra elevation, multiple instances ignored. Actual scheduled action invoked and returned LastTaskResult=0; report cleanup-result-20261018-212700.json Applied=true, zero additional eligible files. User must have an available session; no claim of SYSTEM/unattended logged-out operation.

## Limits and independent publication state
This closes the reviewed cleanup operation, not all application dependency audits or the publication acceptance. As of17:26 local, current MEmu job failed safely before publication on UIAutomator exit137; a subsequent attempt was running in Planejar testes de publicação. No competing live test or Android/session mutation performed in this cleanup round. Do not infer successful posts from cleanup, green CI or identity proof alone.
