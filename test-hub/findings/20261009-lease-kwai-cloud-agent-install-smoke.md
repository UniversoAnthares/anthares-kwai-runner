# Independent GitHub-hosted Android Agent cloud installation smoke
STATUS: RUNNING
AREA: kwai-cloud-android-agent-install
DATE: 2026-10-09
OWNER: chatgpt-cloud-agent-install
LEASE_UNTIL: 2026-10-09T23:59:00Z
HEAD_BASELINE: 3f1dbc6a30e8ab0b605c158d824564e72430a2c4
RESOURCES: .github/workflows/kwai-agent-cloud-install.yml (new file only)
BASELINE_PROVEN: cached Android35 v5 hosted runner restore and Kwai APK splits installed and launched in run 37940202375; latest Anthares Android Agent APK built and uploaded in run 37964111088; no authenticated Android session or real Kwai publication proven.
FAILED_AVOIDED: do not repeat login activities/Android emulator setup from scratch; reuse proven cached snapshot, verified Kwai vault, hosted runner only, no local PC, no user credentials or tokens, no publication, no generic private upload API.
SUCCESS_SIGNAL: one hosted workflow restores v5 snapshot, installs official Kwai package and current Agent APK, opens Agent MainActivity, proves ACTION_SEND video MIME handler registered in installed Kwai manifest. Optional benign ACTION_SEND editor reachability is read-only, no post.
FAILURE_SIGNAL: missing cache, APK build/install fails, agent UI not launched, Kwai share intent unsupported; classify exact stage and do not infer login.
TEST_VALIDITY: hosted cloud Android instance is ephemeral and unauthenticated; this does not solve persistence or user authentication and cannot be called end-to-end publishing.
PEER: GitLab 87307248 main lacks the new workflow path; no mirroring.
CONCURRENCY: new isolated workflow does not overlap active Android login leases or mutate their files.
