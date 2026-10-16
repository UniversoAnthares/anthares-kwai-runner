# CORTES method 3 authenticated fallback — practical proof
STATUS: PROVEN
AREA: live|github|architecture
DATE: 2026-10-16
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38841083860
JOB: 116781069477
COMMIT: 7fa25bafef5745449af81c7bb78b67e63b0edd0a
SUPERSEDES: none

## Objective
Prove the operational fallback defined for CORTES: authenticate to the real YouTube source, download the complete source temporarily on a remote executor, derive the final master, verify the master, and delete the complete temporary source immediately afterward.

## Result
PROVEN on source `9CIk-I_3VhM` (`"A Poética" de Aristóteles - Parte 2 (LIVE)`). Authenticated metadata reported duration 10745 seconds. Method 3 downloaded the complete source temporarily, measured 10744.841 seconds and 1,292,153,794 bytes, produced a 90-second vertical final master, then deleted the complete source before artifact upload.

Final master from the proof run: 13,831,927 bytes, SHA-256 `4ce5276f27484e0e50bebcf06653b9bf021ea655c0888f29fc9f050c3ea8b1d3`.

Decisive signals: `METHOD3_AUTH_METADATA=PROVEN`, `METHOD3_FULL_TEMP_ACQUISITION=PROVEN`, `METHOD3_REMOTE_PROCESSING=PROVEN`, `METHOD3_SOURCE_DELETE=PROVEN`.

Artifact `cortes-method3-authenticated-38841083860` contains `final.mp4`, `result.json` and acquisition log; the complete source is intentionally absent. The final master was subsequently staged on the authorized Windows host at `C:\ProgramData\AntharesPublishCanary\method3\final.mp4` with matching SHA-256.

## Consequence
Method 3 is an operational fallback only. Method 1+2 remains preferred. Publication proof is separate: `social_publish=false` in this run. A real Kwai canary must use the canonical physical Android -> MEmu standby routing, verify exact target account `@lucasrosalem` immediately before the irreversible boundary, and stop fail-closed on any UNCERTAIN result.
