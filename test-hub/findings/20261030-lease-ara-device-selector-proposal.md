# Isolated Windows device reserve selector proposal
STATUS: RUNNING
AREA: ara-windows-selector-proposal (isolated; no deployment)
OWNER: codex ara-selector-proposal-20261030
DATE: 2026-10-30T14:31:53.189792+00:00
EXPIRES: 2026-10-30T15:01:53.189792+00:00
BASE_HEAD: 3018f3fc2c92623778e287aa0d0ecd3bcf5d191a
GOVERNANCE: 84905aefc5589d17
BASELINE_PROVEN: Main and GitLab selector blob d0ea6a1bd17667d8a2bbde0f200d0a012c048f0d; installed selector differs by queue-only safety fix, SHA256 F1FB87520392A8AEB8E8CFCBD8A9CF57FEE59E9776D80F225F2960014AC4C56F. Reserve real device auth/status200, anonymous401, both actual MCP connections authenticated but device disconnected.
FAILED_AVOIDED: Previous administrative application rejected blocked by policy. This task prepares source and isolated tests only; no repeat, alternate execution channel, installation, privilege request, restart, queue job or live deployment. No model artifacts on PC.
SUCCESS_SIGNAL: isolated PowerShell tests preserve primary priority, select independent reserve, skip known shared quota alias, stop401/403, and leave no origin when all fail. Proposal remains draft, not installed or merged.
FAILURE_SIGNAL: wrong priority, authorization bypass, exhausted alias retried, unavailable route returned or any installation side effect.
TEST_VALIDITY: remote CI uses synthetic transport responses and no real credentials/network; this is not Windows production recovery.
