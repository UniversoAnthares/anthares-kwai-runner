# ARA context routing — Cloudflare live, GitHub held for credential recovery
STATUS: PARTIAL
AREA: anthares-remote/windows-identity-routing
DATE: 2026-10-29
RUN: none
JOB: external private incident context-routing-20261029-codex
COMMIT: this feature branch
SUPERSEDES: none

BASELINE_PROVEN: Canonical ARA runs under SYSTEM, while existing Wrangler OAuth is in the owner's Windows profile. Existing user ARA fallback does not route provider-specific CLI commands.
FAILED_AVOIDED: No credential copying, second queue consumer, global PATH/profile interception, canonical-agent restart or publication.
SUCCESS_SIGNAL: Authenticated ARA SYSTEM call executes registered provider under the owner SID and validates the expected Cloudflare account.
FAILURE_SIGNAL: Wrong identity/account, provider denial, uncertain result, duplicate request or surviving owned broker after normal stop.
TEST_VALIDITY: Actual read-only provider identity calls; metadata-only negative-case reporting; no destructive preview deletion, deployment or publication.

## Evidence
- ARA job f1ad7cb1d9b038419e5c4b346d7b0e95: Windows identity stayed SYSTEM; Cloudflare whoami executed under the registered owner SID and validated the expected account.
- Initial credential-printing negative test exposed a GitHub CLI credential in technical tool output because the old server survived a task stop. No secret value belongs in this finding. Owned broker was paused, both exact owned orphan server PIDs stopped, credential routes blocked, output redaction tightened and graceful lifecycle implemented.
- ARA job ec51c2888cf1e9ac9ddcc8398b2eef0a: auth status --show-token, auth token, malformed numeric argument, interactive Cloudflare login and persisted duplicate ID all rejected. Owner-context GitHub and Cloudflare read-only identity probes passed before GitHub quarantine.
- ARA job 225062c0669e9d3370f102c6f989b660: graceful stop returned STOPPED, zero owned servers remained; absent user bridge returned USER_CONTEXT_UNAVAILABLE without SYSTEM fallback.
- GitHub route is now disabled in private machine config until owner renews the exposed credential. Existing unrelated GitHub sessions/processes were preserved.
- Runtime script final pre-governance-update SHA256: 032D0530CA6C8E512D594873D40C263453E6470756668264B53749DC68F8C0CF.
- Local named-pipe ACL admits only SYSTEM and registered owner; runtime code/config are read-only to the limited owner broker; audit contains request IDs, time, service, identity SID, status and governance version, no args or results.
- No Windows password stored, OAuth copied, publishing flags changed or production job dispatched.

## Remaining limits
Cloudflare route is live. GitHub needs credential renewal and revalidation. Owner must remain logged on. Other services and legacy direct shell commands are not automatically covered. The principal queue consumer, existing recovery agents and publisher authorities are unchanged. Source is on a review branch; installed runtime acceptance is separate from main merge.
