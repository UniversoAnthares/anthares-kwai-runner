# QA TikTok WordPress reconstruction — original matrix invalid, inventory baseline recovered
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37405252389; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37405510219
JOB: 112081265008; 112081265283; 112081265316; 112081265365; 112081265376; 112082081484; 112082081584; 112082081641; 112082081657; 112082081706
COMMIT: ee3bc8a054ae31606d37372fe3fcd6eb648c5483; 6d7fa35efb56f1fc5aa0a93fc5fc96f482b05a48
SUPERSEDES: test-hub/findings/20261006-0240-tiktok-wp-filename-reconstruction-running.md; test-hub/findings/20261006-0243-tiktok-wp-inventory-forensics-running.md

## Objetivo
Close the filename-reconstruction RUNNING claim without turning a broken precondition into five false FAILED results, and incorporate the causal successor inventory-forensics run.

## Resultado
Run 37405252389 is HARNESS/TEST INVALID for all five reconstruction variants. Every job emitted TEST_VALIDITY=INVALID because the newest REST video record did not expose media_details.file, which the workflow required before branching.

The causal successor run 37405510219 is valid and 5/5 green. It reached TEST_VALIDITY=OK with 191 live REST video records. It proved:
- 191/191 records report video/mp4;
- 191/191 expose source_url on anthares.us;
- 191/191 expose slug;
- all 191 expose a top-level filename field;
- only 73/191 expose media_details and filesize;
- current date/path samples consistently point into /wp-content/uploads/anthares-clips/YYYY/MM/.

This recovers a valid registry/inventory baseline. It does not prove that any referenced MP4 currently returns usable bytes, so WordPress physical media retrieval remains PARTIAL.

## Evidência decisiva
Run 37405252389: all five jobs emitted TEST_VALIDITY=INVALID.
Run 37405510219:
TEST_VALIDITY=OK COUNT 191 in all five jobs.
MIMES {('video/mp4', 'file'): 191}
HOSTS {'anthares.us': 191}
FORENSIC_SIGNAL=SLUGS 191
FIELDS includes filename:191, media_details:73, filesize:73.
DATE_PATH_SAMPLE shows /wp-content/uploads/anthares-clips/2026/10/... and /2026/09/... paths.

## Consequência
Do not label the five filename reconstruction branches FAILED and do not rerun them unchanged. The missing media_details.file precondition invalidated that matrix. Any future WordPress retrieval experiment must branch from the valid 191-record inventory and may use top-level filename/date/slug evidence without requiring media_details.file. The TikTok canary no longer depends on this WordPress retrieval path because the synthetic cloud MP4 harness is independently PROVEN.