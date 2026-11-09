# AOI #08 — transferência de cota GitLab CI → GitHub Actions
STATUS: PROVEN
AREA: ci-quota-failover/gitlab-to-github
ITEMS: [8]
DATE_UTC: 2026-11-09T03:21:07Z
SOURCE: GitLab project 87307248, pipeline 3010062525, SHA ca4e7a0dbd2c7a72ba0b4ae953688213f49f845d; failed terminal, six jobs ci_quota_exceeded, none started.
DISPATCH: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42555715562 — completed/success, DISPATCH_ACCEPTED_LEDGER_ACKED, HTTP 204, Neon OIDC reservation/CAS.
SUCCESSOR: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42555737306 — completed/success, GITLAB_SOURCE_SHA=ca4e7a0dbd2c7a72ba0b4ae953688213f49f845d, CORTES_GITLAB_CI_GITHUB_BACKUP=PASS.
SIGNED_RECEIPT: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42555900410 — completed/success, Neon FALLBACK_CONFIRMED, receipt_confirmed=true, successor_run_id=42555737306.
NEON_READBACK: public.anthares_ci_quota_attempts 21/21 FALLBACK_CONFIRMED and 21/21 receipt_confirmed=true.
OTHER_REAL_CASE: GitLab 3010066125 SHA 27beeff7fba0341ae0ebb2ee681d7de975a56597 → GH 42553848443 success; signed receipt run 42553989119.
HISTORICAL_CORRECTION: earlier GitLab 2994547840 had mismatched checkout; exact source GitLab SHA bb64681264e6ca6c1665b0d398dcfd7c101225e3 validated in GH 42554841361 and signed confirmation 42554921328, preserving previous successor metadata.
PATCHES: #2227 precise original source; #2228 event-only GitHub fallbacks (CORTES and private), zero periodic schedule/push; #2229 one authenticated real historical quota incident; #2230 retain 15-minute cooldown except exact distinct-SHA after terminal prior job.
ADDED_BILLING: no purchases, upgrades or authorized charges. MEDIA_PUBLICATIONS: 0. NEW_INFRASTRUCTURE: 0. PC_STAGING: 0.
SCOPE: Proves real GitLab CI terminal quota transfer with independent GitHub execution and Neon fencing/receipt. Separate provider adapters or unrelated publishers require their own evidence.
