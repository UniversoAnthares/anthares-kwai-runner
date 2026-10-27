# Lease — isolated Android routing-contract schema fix
STATUS: RUNNING
AREA: github / ci-android-routing
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40494510557
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40494510557/job/122156438512
COMMIT: ed5ae1100535e745ab95555d9ba1b3f778d7734f
SUPERSEDES: none

Owner: ChatGPT 20261027 android-routing-schema. Lease scope limited to the retired-CircleCI routing-contract assertions in .github/workflows/anthares-android-replacement.yml. Expires 30 minutes after this GitHub file commit; no license to change Android publication, real-device jobs, Neon or account credentials.

BASELINE_PROVEN: main JSON keys include browser_execution.backend_priority and retired.circleci, and providers.gitlab_ci.active=true. GitLab peer has identical workflow blob bbb2666bb73ca8792f528a60ae3ec2ccee616927.
FAILED_AVOIDED: run 40494510557 / job 122156438512 failed KeyError: 'priority' from stale browser_execution.priority; fix field references directly without reverting routing manifest.
SUCCESS_SIGNAL: hosted routing-contract job prints CIRCLECI_RETIRED_ROUTING=PASS after Python unit tests.
FAILURE_SIGNAL: assertion fails against current JSON schema, or branch/lease/manifest changes concurrently.
TEST_VALIDITY: Android emulator/job separately gated by existing workflow. A routing test failure is not proof of login or publication failure.
