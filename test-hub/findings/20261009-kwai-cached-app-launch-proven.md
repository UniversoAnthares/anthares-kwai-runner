# Kwai real app launch after v5 cached Android snapshot
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37940202375
JOB: 113852336706
COMMIT: 2ef64cbc80ac3fc1728f61c60380f5275fc3c9ea
SUPERSEDES: 20261009-kwai-fastpath-to-app-launch-integration.md

## Result
Workflow SUCCESS. V5_ACTUAL_LOAD=true; V5_RESULT=PROVEN_SUB10. Vault SHA256 verified; adb install-multiple succeeded; com.kwai.video installed and launched. topResumedActivity=ActivityRecord{597fc20 u0 com.kwai.video/com.yxcorp.gifshow.tiny.TinyLaunchActivity t8}. KWAI_APP_INSTALL=PROVEN; KWAI_APP_FOREGROUND=true; KWAI_APP_READY_TOTAL_SECONDS=75; KWAI_INSTALL_LAUNCH_SECONDS=44; KWAI_APP_LAUNCH_ACCEPTANCE=PROVEN_NO_AUTH_CLAIM.

## Scope
This proves installation and foreground launch, not MAIN, authentication, identity, persistent session or publishing. No login-agent files modified; no local PC used. Preserve v5 as PROVEN; next step is session/identity work by authorized lease holder, not another startup benchmark.
