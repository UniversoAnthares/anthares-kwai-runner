# AOI-7 lease — Forgejo keepalive process cap and status receipt
STATUS: RUNNING
OWNER: ChatGPT 2026-11-11
UTC: 2026-11-11
SOURCE: UniversoAnthares/anthares-kwai-runner:tools/forgejo_keepalive.sh
SOURCE_BLOB: 27b95a09e3431a42c51221cc9c7c8b7b73120ff4
BRANCH: fix/forgejo-keepalive-process-cap-20261111
BASE: 83f0d51695b84d1be85d88b0104fbf5171f8beb0
EVIDENCE: Hostinger authenticated file manager read 2026-11-11. Forgejo daemon starts 11:20,12:25,13:30,14:35,15:40,16:45,17:50,18:55 UTC and each returns local /api/v1/version HTTP 200; source mirror receipt 18:43 UTC 15/15, failures []. Hostinger NPROC most recent hour peak 62 versus contractual base 80, temporary 120 boost still active. Forgejo historical log shows runtime/cgo pthread_create failed Resource temporarily unavailable at 11:10 UTC; keepalive script current no GOMAXPROCS limit or persistent health tick.
SCOPE: Change only existing keepalive launch environment to GOMAXPROCS=2 (reduce Go scheduler CPU concurrency in constrained shared hosting); add bounded single JSON health-state receipt updated atomically once each 5-minute cron without external date subprocess. Preserve healthy daemon, no kill/restart of live process, credentials, refs, forced Git, public endpoints, cron frequency or costs. Existing refusal of public HTTPS probe must not be circumvented.
SUCCESS: bash -n test, regression tests for unchanged recovery guards, source and live SHA verification after hPanel save; persistent health receipt on next scheduled ticks; independent 15/15 receipt unaffected. Unknown future 65min process death remains partial pending elapsed-time observation.
FAILURE: preserve existing service and report read-only current state; do not repeat denied Hostinger executor or bypass hosting permissions.
