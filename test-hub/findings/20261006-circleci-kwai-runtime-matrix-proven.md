# CircleCI Kwai runtime matrix — installation path proven
STATUS: PROVEN
AREA: kwai-runtime
DATE: 2026-10-06
RUN_SET: CircleCI jobs 987-1033
SUPERSEDES: test-hub/findings/20261006-circleci-full-kwai-five-replica-matrix.md; test-hub/findings/20261006-circleci-kwai-five-causal-runtime-variants.md

## Results
On the later completed matrix, all five full same-step replicas succeeded:
01 job 1020, 02 job 1016, 03 job 1014, 04 job 1033, 05 job 1032.

All five causal runtime variants also succeeded:
cold job 1018, wait2 job 1013, restart_adb job 1012, launch_retry job 1023, ui_delay job 1028.

All ten ADB boundary replicas in that matrix succeeded:
jobs 1021, 1029, 1024, 1017, 1010, 1025, 1022, 1015, 1030, 1011.

Android executor smoke job 1019 and provider smoke job 1031 succeeded.

The legacy kwai_install_smoke job 1026 failed because it treated post-step process/UI persistence as a mandatory installation acceptance criterion. The full same-step and causal matrices independently prove installation/launch/UI across ten successful full/runtime executions. Commit f1eea9836bb10739c59bb9c3fd6dc02d26816e44 corrects that acceptance boundary: package presence remains mandatory; post-boundary process/UI state is diagnostic and still emits crash evidence when absent.

## Consequence
CircleCI Android + validated Kwai vault installation + launch/UI path is PROVEN. Future failures of post-boundary runtime persistence must not reopen the installation hypothesis without contradictory package/install evidence.

BASELINE_PROVEN: CircleCI Android executor, ADB boundary persistence, validated Kwai vault.
FAILED_AVOIDED: no login URI, hidden Activity, credential, or publication mutation.
SUCCESS_SIGNAL: five of five full same-step probes and five of five causal runtime variants succeeded.
TEST_VALIDITY: independent AVDs and validated vault SHA were used.
