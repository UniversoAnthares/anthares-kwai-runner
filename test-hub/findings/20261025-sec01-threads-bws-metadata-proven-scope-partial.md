# SEC-01 R07.6 item 06 — Bitwarden Threads scoped metadata proven; administrator-only fields outstanding
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-25
OWNER: chatgpt-sec01-threads-bws-metadata-qa
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40235027169
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40235027169/job/121294643997
COMMIT: 851afd6393a27029da276faabbe88ad1d8f3f02f
SUPERSEDES: 20261025-sec01-threads-bws-metadata-running.md

## Scope
One CORTES account only: Threads universoanthares, credential reference in config/threads-cloud-auth-reference.json, existing GitHub Actions BWS_ACCESS_TOKEN. QA branch chatgpt/sec01-threads-bws-metadata-qa-20261025 only. No production changes, no secret contents, no publishing, no queue access, no new privileges.

## Verified evidence
- Earlier attempt 40234560464 proved SEC01_AUTH=PASS, SEC01_THREADS_SECRET_METADATA=PASS, SEC01_SCOPE_PRESENT=PASS but failed during organization-wide listing; SDK and state cleanup PASS.
- Narrowed assigned-project audit 40234775556: conclusion SUCCESS and SEC01_AUTH=PASS; SEC01_THREADS_SECRET_METADATA=PASS; SEC01_SCOPE_PRESENT=PASS; SEC01_THREADS_PROJECT_METADATA=PASS; SEC01_METADATA_AUDIT_SCOPED=PASS; SEC01_EPHEMERAL_CLEANUP=PASS.
- Stronger same-scope audit 40235027169: conclusion SUCCESS with SEC01_THREADS_PROJECT_NAME=Anthares_Automation_VERIFIED, and all previous scoped PASS signals. Only metadata of a referenced project and secret accessed. Does not establish org-wide listing.
- Historical account design names anthares-automation as the intended machine account; the SDK successfully authenticated an access token issued to a machine account, but does not establish that this token is attached to that name. Do not elevate history to provider verification.
- Bitwarden Secrets Manager free tier publicly documents up to 3 projects and 3 machine accounts; the actual subscription plan/available quota of the Anthares Secrets organization has not been inspected in an authorized admin console.
- Local policy.py preflight PASS; private governance version 2e28d54043d6bad1 and local version f6fc9ca59a96e451 differ, without synchronization or overwrite.

## Remaining acceptance gates
(1) Read Bitwarden machine-account administrative record: actual name/id and project permissions for the existing GitHub BWS_ACCESS_TOKEN, without exposing the token.
(2) Read actual organization billing/subscription machine-account quota and current allocated/used counts from the authorized Bitwarden Admin Console (not inferred from advertised plan).
(3) Preserve the org-wide enumeration failure and do not retry it by credential escalation or a different identity. SEC-02 cross-identity negative access verification is a separate item and is not proven by this run.
(4) Reconcile concurrent governance manifest divergence before syncing documentation.

## Consequence and rollback
SEC-01 scoped Threads project+secret inventory is proven by live CI; overall R07.6 item 06 remains PARTIAL until admin fields (1),(2) are independently verified. Branch is unmerged, main and production untouched; rollback is branch closure/deletion after preserving linked evidence. No token values, secret values or credential payloads in this finding.
