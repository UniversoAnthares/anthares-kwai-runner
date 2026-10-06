# Multi-executor CI hub

GitHub remains the canonical source of truth. Provider-local logs are immutable run artifacts and are summarized here by provider.

Providers:
- GitHub Actions: test-hub/ + Actions logs
- CircleCI: ci-hub/circleci/
- GitLab CI: ci-hub/gitlab/
- Bitrise: ci-hub/bitrise/

Every provider run must emit:
PROVIDER=<name>
SOURCE_SHA=<git sha>
TEST_VALIDITY=<marker>
SUCCESS_SIGNAL=<marker or NONE>
FAILURE_SIGNAL=<marker or NONE>

A provider green status alone is never PROVEN. Secrets, credentials, cookies and session payloads must never be written here.
