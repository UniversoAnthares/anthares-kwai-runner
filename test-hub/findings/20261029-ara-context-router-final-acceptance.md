# ARA context router — final installed acceptance
STATUS: PARTIAL
AREA: anthares-remote/windows-identity-routing
DATE: 2026-10-29
RUN: none
JOB: ARA 1f9701ea762371eb5786853cd92522a6
COMMIT: this branch
SUPERSEDES: 20261029-ara-context-router-partial.md

## Final evidence
The corrected installed source completed actual ARA CMD -> hidden Windows PowerShell -> owner broker -> Cloudflare identity verification. Job 1f9701ea762371eb5786853cd92522a6 returned completed, exit 0, timed_out=false, ok=true, owner Windows identity and CLOUDFLARE_ACCOUNT_VERIFIED for the configured account. No production mutation occurred.

Startup governance hash verification now uses .NET SHA256 directly, avoiding an unavailable Get-FileHash module in the scheduled identity. CLI framing reads exactly one bounded JSON line rather than waiting indefinitely for pipe EOF. whoami reuses its already verified identity preflight instead of issuing it twice. The owned task propagates failure exit codes for its configured restart policy. Windows PowerShell is the validated runtime; direct PowerShell Core invocation is not homologated.

Earlier interrupted requests were read-only and are retained in the metadata ledger; do not resend their IDs. Only exact owned orphan server PIDs were stopped during recovery. Main ARA agent, other agents, user applications and publishers were preserved. Graceful stop, no-context failure, duplicate rejection, invalid arguments and credential-command rejection were proven in the earlier finding; four synthetic redaction fixtures passed in memory.

Central governance local version 93bb656ac10c5640 and 210 repository copies updated. Eight stale non-repository entries cause 32 documentation audit failures; registry cleanup was outside scope. Private GitHub governance publication follows its existing reviewed publisher and is not asserted complete here.

Cloudflare route is operational. GitHub route remains disabled until owner credential renewal after the initial technical-output exposure described in the earlier finding. No secret value is recorded here. Other providers, user-logoff execution and transparent interception of legacy commands are not claimed.
