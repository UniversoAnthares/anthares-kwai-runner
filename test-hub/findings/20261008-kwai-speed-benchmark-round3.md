# Kwai speed benchmark round 3 — warm Android boot proven
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37858963753
JOB: 113589864410
COMMIT: 42b660ef462f7d10decf693bacbd81d259d9579e
SUPERSEDES: 20261008-kwai-speed-benchmark-round2.md

## PROVEN
Hosted GitHub Actions job completed SUCCESS. Android image cache hit: kwai-speed-android35-google-apis-x86_64-v1, ~1572 MB restored successfully. Kwai vault cache hit: kwai-speed-vault-96650454576a2cf5-v1, ~42 MB restored successfully. Android AVD created, emulator launched, adb sys.boot_completed gate passed. Dedicated emulator binary cache kwai-speed-emulator-ubuntu24-v1 saved successfully at end of job.

## TIMING EVIDENCE
Logs: Android image cache restore started 23:21:28Z and completed 23:21:49Z (~21 seconds); Kwai vault cache hit 23:21:51Z and restored by 23:21:53Z (~2 seconds). Overall job steps started after 23:21:28Z and cache save completed 23:22:54Z; this is not equivalent to TOTAL_SECONDS because the full GitHub Step Summary values are not in decoded job logs. Do not invent cold boot or total timing figures. Next run should capture machine-readable timing output as well as Step Summary.

## NEXT
Confirm three cache hits on another hosted run; measure PREP_TOTAL_SECONDS, COLD_BOOT_SECONDS, TOTAL_SECONDS. Do not modify login agent files. No login, account authentication, publishing or reusable Android AVD snapshot proven.
