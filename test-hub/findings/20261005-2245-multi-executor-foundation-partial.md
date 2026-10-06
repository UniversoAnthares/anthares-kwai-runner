# Multi-executor foundation staged
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-05
SUPERSEDES: test-hub/findings/20261005-2235-lease-kwai-login-multi-executor-foundation.md
BASELINE_PROVEN: GitHub remains canonical source/hub; provider-specific configuration can live in the same repository.
FAILED_AVOIDED: no PC dependency; no external-provider success inferred from config-only commits; GitLab free path does not rely on Premium external-repository integration.
SUCCESS_SIGNAL: canonical repository now contains ci-hub/{circleci,gitlab,bitrise}, shared provider smoke contract, .circleci/config.yml, .gitlab-ci.yml and bitrise.yml.
FAILURE_SIGNAL: external execution has not yet been observed because provider-side account/repository authorization is not established in available tools.
TEST_VALIDITY: configuration presence is integration readiness only. CircleCI/GitLab/Bitrise become PROVEN only when their own run emits TEST_VALIDITY=PROVIDER_SHELL_READY and SUCCESS_SIGNAL=PROVIDER_HUB_OK.

READY: NO. AUTHENTICATED: NO.
NEXT: authorize/connect the GitHub repository in CircleCI and Bitrise; create/import a GitLab project on the free path; then run provider smoke and promote the Android runtime suite independently on each provider.
