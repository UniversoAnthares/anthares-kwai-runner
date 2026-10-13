# Android executor routing — independent external proof
STATUS: PROVEN
AREA: executor-routing
DATE: 2026-10-12
PIPELINE: https://gitlab.com/universo-anthares-group/anthares-kwai-runner/-/pipelines/2940629084
JOB: 17126934205

## Result
A fresh independent GitLab runner cloned canonical GitHub `main` and executed the merged routing contract.

All six unit tests passed. Dynamic checks also proved:
- normal state selects `circleci`;
- CircleCI queue at 91 seconds selects `bitrise`;
- CircleCI+Bitrise unhealthy selects `firebase_test_lab`;
- missing provider live state selects `NONE` and exits fail-closed;
- GitHub Actions remains `retired_from_android_execution`.

Decisive signal: `ANDROID_EXECUTOR_ROUTING_EXTERNAL_PROOF=PASS`.

## Active Android order
`circleci -> bitrise -> firebase_test_lab`

This proof validates routing behavior only. Bitrise and Firebase still require their own live executor acceptance before they may report `ready=true` in production state.
