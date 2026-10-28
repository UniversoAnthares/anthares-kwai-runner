# Item 6 — isolated Forgejo read-only OIDC patch
STATUS: PROVEN
AREA: architecture/forgejo-readonly-identity
DATE: 2026-10-28
RUN: https://anthares.us/forgejo/anthares-admin/anthares-tiktok-forgejo/actions/runs/7
JOB: Forgejo global run 290; runner anthares-tiktok-hostinger-readonly
COMMIT: e32a2bba7ad086d5e0eccd7b7b8d6a54b9e20fda
SUPERSEDES: none

BASELINE_PROVEN: Branch 4494ea971df658b5ae934c3c233936346cfdd678, Vercel dpl_2ew3WQvu8W2n3utFUKHMPGHRQ7Rb, sandbox OIDC signature proof.
FAILED_AVOIDED: Read-only TikTok workflow run 278 rejected by sandbox-only identity allowlist. Exact owner patch adds only item6-hostinger-readonly-standby.yml.
SUCCESS_SIGNAL: FORGEJO_TIKTOK_READONLY_SCOPE_TESTS_PASS=13; real signed JWT accepted by Vercel; terminal success.
FAILURE_SIGNAL: Scope/signature failure, concurrent endpoint change or production side effects.
TEST_VALIDITY: External isolated Hostinger checkout, original patch SHA256 A0813A4BA56E4F299BC26B69C872CC0BC0461A5D83C1F236468CFC9D0901CCB8. git apply --check passed. Governance version 223433740e807a90. Private RUNNING lease and test evidence stored before testing in Hostinger incident item6-oidc-patch-20261028-codex.

## Evidence
- 13 OIDC checks passed, including denial of tiktok-forgejo-universo.yml and tiktok-forgejo-lucas4.yml, wrong audience/event/ref/owner, expiry, foreign repository, POST and signature tampering.
- Vercel production dpl_GnZzoFiPi5BKGCZGayLJD7kU3oet READY at exact code commit above.
- Forgejo run 290 (repository index 7), commit 4386072f492c9498cef066c27a4820e3c88014fd, terminal success 2026-10-28T21:22:42Z. Workflow file unchanged from inspected be67f11c13c2988c2cf89e97a93a54e920f3a16f.
- FORGEJO_OIDC_LIVE_SIGNATURE_AND_SCOPE=PASS
- VERCEL_FORGEJO_REAL_JWT=PASS (HTTP 200 authenticated identity response)
- ITEM6_HOSTINGER_TIKTOK_SIGNED_OIDC=PASS
- ITEM6_CORTES_PRODUCTION_GATE=DISARMED
- ITEM6_NO_SOCIAL_PUBLICATION_OR_LEDGER_MUTATION=PASS
- Anonymous identity endpoint remains HTTP 401; /health HTTP 200.
- No credentials, publication flags, Neon queues or TikTok sessions changed.

## Limits
This closes only the owner-requested read-only OIDC 401. Publisher workflows remain outside the identity-proof allowlist; no publisher workflow was run. ITEM6_TIKTOK_EXTERNAL_SESSION_IDENTITY=NOT_VERIFIED. This is not whole-item social migration homologation.
LEASE: CLOSED after proof; own temporary external checkout removed, sanitized incident evidence retained.
