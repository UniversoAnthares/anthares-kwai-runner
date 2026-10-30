# Independent read-only Hostinger diagnostics deployed and verified
STATUS: PROVEN — LIMITED READ-ONLY COMPONENT; FULL MIGRATION NOT COMPLETE
AREA: cloudflare-control / independent-readonly-service
DATE:2026-10-30
OWNER:codex independent-readonly-service-20261030
GOVERNANCE:84905aefc5589d17
SUPERSEDES:test-hub/findings/20261030-lease-independent-readonly-service.md
LEASE:CLOSED

## Implemented scope
PR2003 merged normally, mergea68837a79ac90efda713f8eb9212fa497a59fc5e. Distinct ANTHARES-HOSTINGER executor dispatch supports only system_info/session_status/capabilities. Hostinger PHP endpoint verifies the existing gateway Ed25519 signature through its fixed bounded Node handler. No client-supplied program/path/command. Default Windows dispatch, Vercel, Neon queues, OAuth credentials and signer keys preserved. No model call, job worker, second ledger, paid resource or Windows action.
PR2006 merged normally; private argument-free owner operator CLI uses existing owner OS/SSH session. The public HTTP endpoint still requires its normal signature. This is a separate intended owner authentication boundary, not a generic anonymous execution endpoint or an alternative for the refused Windows action.

## Isolated tests and deployment
https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41105072005:21 tests21 pass0 fail. Includes real Ed25519, forged/expired/path/method rejection, no retries on401/403/quota/error, correct limits, real PHP-to-Node child execution/cleanup and OAuth MCP dispatch; unsupported write rejected before any host/control network request.
https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41105071819 SUCCESS: existing owner/PKCE/replay/scopes/transport acceptance preserved.
https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41106423584 SUCCESS:22 tests including owner CLI output and rejection of every argument.
Canonical deployment https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41105549289 SUCCESS, version217c6bc5-d149-4c81-874b-99395615e2e1; ANTHARES_CLAUDE_BRIDGE_DEPLOY_ACCEPTANCE=PASS and ANTHARES_CLAUDE_BRIDGE_ANON_MCP_DENIED=PASS.
Private Hostinger source/config outside public_html, owner-only. New public endpoint only; no existing file overwritten. Immutable source hash readback verified. Only the public signer verification key pinned; no model/device/OAuth/private signing credential copied.

## Real acceptance
Anonymous GET https://anthares.us/anthares-independent/status.php returned401 unauthorized.
Actual system_info(device_id=ANTHARES-HOSTINGER) via Anthares Remote Cloudflare at18:18:33Z and Anthares Remote — Cloudflare at18:19:01Z returned ok/connected/read_only true, provider Hostinger, runtime Node24.22.1/Linux/x64, existing gateway reachable and Kilo executable.
Actual session_status same device at18:19:03Z returned queue_state not_applicable_for_read_only_diagnostics and counts null; no invented zero-job proof for a service with no job queue.
Actual remote_exec with that external device returned external_executor_operation_not_supported. This was an EXPECTED_NEGATIVE service contract test, no command ran and no alternate route was attempted.
Remote operator CLI executed through existing SSH, exit0, provider Hostinger, read_onlytrue, gateway_reachabletrue, kilo_cli_executabletrue, client anthares-operator-cli. No OpenAI or model request required. Source536f46ce6acb95ae9231fd4da59f9f0da7427c05; CLI SHA2565d3546e6d78e32bca97ba6d79afe20df2b76f189a636189bd8ac4a80b133fc83.
Owned temporary status handlers remaining0 after acceptance; no new background service. Existing gateway socket remained0600. Private deployment/operator receipts retained on Hostinger; no local work files created.

## Limits
Only read-only diagnostics are implemented here. This is not a durable job executor, media/voice runtime, publisher migration, independent MCP-client OAuth consent or proof of the account CPU/RAM/storage allocation. Host hardware observations are explicitly shared-host values. Inference is not_tested in this endpoint; prior governed Kilo canary was cancelled for quota, not retried.
Original Windows endpoint remains disconnected and its blocked administrative repair/selector proposal was not repeated. No scheduled routine was retired by this component. Full service and all local routine migration remain open under private governance planPR51. Existing shared Neon remains a common dependency of other job operations.
