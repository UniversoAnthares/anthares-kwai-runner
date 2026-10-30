# ARA refresh temporary backend error classification
STATUS: RUNNING
AREA: cloudflare-control / ara-oauth
OWNER: codex ara-oauth-refresh-disconnect-20261030
DATE: 2026-10-30T13:53:32.598266+00:00
EXPIRES: 2026-10-30T14:23:32.598266+00:00
BASE_HEAD: a5bd33a40aa0aee8ea4e1d2021a4be9aa9adc814
SOURCE_BLOB: c37039e6bdf72bd8f7094c5c599751601ea4df5f
PEER: GitLab main same index blob, checked read-only.
GOVERNANCE: 84905aefc5589d17
BASELINE_PROVEN: User reports both accounts require reconnect after refresh. Both capabilities currently authenticate but device offline. Source converts all replay backend errors to false then invalid_grant400. Previous owner cookie fix and reserve remain preserved.
FAILED_AVOIDED: No repeat owner cookie change, no token/key rotation, no refresh replay relaxation, no duplicate executor.
SUCCESS_SIGNAL: regression proves backend outage returns503 temporary error, token remains unused when consume not applied, successful retry rotates, replay remains400. Existing owner/PKCE/scope tests pass; canonical deploy health and anonymous401 preserved.
FAILURE_SIGNAL: temporary outage still returns invalid_grant, replay accepted, changed valid credentials or failed regression.
TEST_VALIDITY: isolated mocked backend tests with synthetic tokens in remote CI; not proof of actual ChatGPT persistence. Real root cause remains under investigation; no OAuth400 captured in sanitized tail.
