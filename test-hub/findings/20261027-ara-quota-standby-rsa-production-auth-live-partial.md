# Anthares Remote — standby de cancelamento por quota em produção (27/10/2026)
STATUS: PARTIAL — CONTROL AUTH LIVE, EXTERNAL PROVIDER CREDENTIALS MISSING
AREA: CI quota / Anthares Remote / Neon / Vercel
DATE: 2026-10-27
RUN: Windows task Anthares CI Quota Cancel Standby
JOB: Windows local STATUS at 2026-10-27T15:53:03Z
COMMIT: 016c7a816e79e18c77e99cf45c63e0853209ffeb
SUPERSEDES: test-hub/findings/lease-20261027-ara-quota-cancel-standby-chatgpt.md

## Fonte operacional
- Main PR #1571 and #1574 merged. Windows script `anthares-remote-agent/windows/ci-quota-cancel-standby.ps1`, deployed local to `D:\AntharesWork\AntharesRemote\source\ci-quota-cancel-standby.ps1`.
- Windows Scheduler `Anthares CI Quota Cancel Standby`: task registered under `SYSTEM`, recurrence every 15 minutes, IgnoreNew, maximum runtime 3 minutes. First scheduled task execution LastTaskResult=0. Script independently executed under SYSTEM with no error.
- RSA-3072 private key generated locally and encrypted by Windows DPAPI at `D:\AntharesWork\AntharesRemote\secrets\ci-quota-remote-rsa.dpapi`, restricted to SYSTEM + Administrators; private XML never transmitted or committed. The **public** verification key was registered in Vercel production `ANTHARES_REMOTE_QUOTA_PUBJWK`.
- Live Vercel production deployment `dpl_Fqbgk75EFQrQ6mS83gPfnd8DiQ5p` READY; endpoint `/api/provider-cancel` shares the production `public.anthares_ci_quota_attempts` Neon ledger with existing GitHub OIDC watcher. Remote signs timestamp+canonical payload with RSA-SHA256; server validates fixed hostname, signed body and time skew <=120 sec.
- **Actual independent end-to-end identity/DB receipt:** local SYSTEM standby reported `auth=READY_DPAPI_SYSTEM`, `controller=READY_RSA_NEON` after live signed HTTPS request. Vercel validated RSA and selected the restricted database role `anthares_ci_quota_limited` with main quota table present.
- GitHub Actions watcher last observed run 40530808280 SUCCESS but `APPVEYOR=NOT_CONFIGURED` and `BITRISE=NOT_CONFIGURED`. Remote standby likewise `appveyor=NOT_CONFIGURED`, `bitrise=NOT_CONFIGURED`, `events_claimed=0`, `remote_cancellations_confirmed=0`, `fallback_dispatched=false`.
- Provider-specific DPAPI credential files `ci-quota-appveyor-token.dpapi` / `ci-quota-bitrise-token.dpapi` and the three config IDs `appveyor_account`, `appveyor_project`, `bitrise_app_slug` remain absent/unpopulated. Local config is `D:\AntharesWork\AntharesRemote\state\ci-quota-standby.json`. Existing unrelated Anthares Remote GitHub issue-queue secret was deliberately not reused.

## Safety and anti-duplication
- Remote and GitHub both must win the SAME cross-host Neon atomic INSERT on attempt_id provider+target, and must report with same fencing owner UUID. No duplicate remote cancellation permitted on an already claimed attempt.
- Provider remote status, main SHA, project/repo and structured provider quota code are required before claim and again before attempting original cancellation. Uncertainty is persisted as `CANCEL_UNCONFIRMED`; no successor dispatch, no publishing, no paid plan change, no inferred quota from HTTP500.
- Missing provider credentials block scans before any mutation. A working remote identity does NOT prove AppVeyor or Bitrise cancelation against a real build. No synthetic incidents generated and no side-effectful job run created.

## Acceptance still pending
1. Authorized AppVeyor and Bitrise API credentials plus exact immutable project IDs must be installed in local SYSTEM DPAPI (and preferably GitHub Actions secrets/vars too). Do not paste tokens into Git, ARA Issues, logs or chat.
2. A genuine provider quota event needs remote cancellation receipt, verified terminal status and independent DB state confirmation. A real confirmed quota event has not yet been observed for these two providers.
3. Other CI platforms still need provider-specific adapters; global cancellation rule remains partial. Existing GitLab real quota failover proof remains separate.
