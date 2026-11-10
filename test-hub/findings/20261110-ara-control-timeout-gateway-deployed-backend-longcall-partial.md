# ARA control timeout: gateway deployed; synchronous long-call backend remains partial
STATUS: PARTIAL
AREA: cloudflare, ara-control
DATE: 2026-11-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42867784450
JOB: Hosted validate/deploy
COMMIT: b58dc14290e5f6c90a4e29392efb7044af09a3c8
SUPERSEDES: none

## Evidence
- PR #2316 merged the gateway transport fix: 15,000 ms default preserved, bounded request timeout up to 150,000 ms. One-shot POST semantics unchanged.
- Isolated source QA: seven timeout boundaries and one synthetic single-POST with a 132,000 ms timeout passed.
- GitHub Actions run 42867784450: validate SUCCESS, deploy SUCCESS. Approved exact SHA used in emergency recovery mode because two unrelated main commits advanced concurrently. Recovery workflow returned to disabled state.
- A read-only 17-second synchronous command still produced `control 500: internal_error`. Do not classify all long synchronous commands as fixed.
- Existing ARA detached execution was validated: encoded PowerShell job 87bc6dbbfc9fd9a3 completed with exit_code 0 and returned Cloudflare deployment metadata; the earlier unencoded CMD quoting failed.
- Worker `anthares-reserva-browser` has a secret binding named `OWNER_APPROVAL_HASH`. The owner login screenshot reported `Código inválido`. The secret value was not read, logged, or rotated; authentication remains pending.

## Consequence
Use the ARA detached job path for long administrative commands and reconcile each job status/receipt. Further investigate the standby's synchronous `/v1/mcp/execute` HTTP 500 separately. Do not replay side-effectful calls with unknown outcome. No media, TikTok publication, or credential changes occurred during this fix.
