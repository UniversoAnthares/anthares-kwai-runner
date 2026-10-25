# Test Hub — CORTES R07.6 items 08–10: provider audit + real QA race/ACL
STATUS: PARTIAL (ISO-03 QA accepted after external CI; ISO-04/ISO-06 provider gates pending)
AREA: control_plane/qa and network-isolation
DATE: 2026-10-25 UTC
JOB: cortes-r076-iso03-shadow-20261025
BASE_COMMIT: 05ae946b79949cb6d43e4134972c10943c9b62a1
OWNER: ChatGPT, user's explicit request, governed version f6fc9ca59a96e451 (218/218 workspaces valid)

## Item 08 — network-specific Environment/secret/CI/deploy
- TikTok GitHub Environment `cortes-tiktok-lucas4` was NOT created: earlier administrative PUT was blocked by security settings, and read-only verification showed it absent. No retry by another controller.
- `TIKTOK_LUCASROSALEM4_STORAGE_STATE` remains a repository-level secret; real environment-scoped custody/restriction, separate deploy identity and cross-network negative tests are unproven.
- PR #1332 contains static contract and read-only CI but was not merged or deployed. **08 remains PARTIAL.**

## Item 09 — Neon QA, SQL privileges/RLS
- Neon connected project `purple-flower-35918989` (anthares-ara-ha), production branch `br-crimson-unit-b89nau08`; read-only inventory found 37 CORTES relations and `cortes_tiktok_lucasrosalem4_publications` with RLS=false, FORCE=false. NO production DDL.
- Existing QA branch `br-quiet-unit-b8w1tqmf` `qa-cortes-rls-isolation-20261024-chatgpt` already includes canary `cortes_rls_canary_20261024`, RLS=true, FORCE=true and policies for Threads and Instagram, but both existing executor roles are NOLOGIN; therefore no independent operational login proof.
- Creating a distinct QA *project* was denied by security settings, so no duplicate project or controller bypass.
- We created two new roles ONLY in existing QA branch to attempt a TikTok/Kwai principal test. Neon API provisioned them with unwanted BYPASSRLS=true, CREATEDB=true, CREATEROLE=true. Attempt to strip privileges via SQL returned `permission denied to alter role`. We immediately deleted ONLY our two freshly created QA roles and verified they are absent in Neon role listings and catalog. Neither was given access to production/workflows. No privileged leftover.
- A new empty synthetic QA table `public.cortes_r076_identity_fence_qa` was created before role attestation. No GRANT, RLS policy or rows were applied; it is not used for live publication and should NOT be claimed as isolated.
- Missing: two real LOGIN roles with NOBYPASSRLS, FORCED RLS and observed SELECT/INSERT/UPDATE/DELETE positives and negatives. **09 remains PARTIAL.**

## Item 10 — isolated practical shadow acceptance
- Created new standalone QA-only `control_plane/qa_iso03_fenced_queue.py` and seven tests in `control_plane/test_qa_iso03_fenced_queue.py` with a checked sentinel, SQLite persistent transaction fencing, token digest, generation, unique job/effect IDs, and `uncertain` never automatically requeued.
- Actual isolated test (Linux disposable root CI equivalent): two concurrently started worker calls, one lease obtained, one rejected/no work; after started and confirmed one durable effect exists and re-confirm fails; idempotent enqueue does not duplicate.
- Two distinct POSIX UIDs in disposable QA own separate chmod 0700 network dirs: each ALLOWED writing its own tenant SQLite DB; Kwai UID denied access to TikTok directory, TikTok UID denied access to Kwai directory, including forged target constructor. No secret or admin token is stored in test.
- Kwai fanout shadow creates only four deterministic no-write intents; no Neon insert, trigger alteration, external publication, media fetch or deploy.
- 7/7 tests PASS in isolated local Linux execution, pending GitHub-hosted external run at PR open.
- This proves item 10's small QA package; DOES NOT enforce ACL on the current Windows SYSTEM publishers or certify production cutover.
- Rollback: close unmerged PR and delete QA branch; all temporary SQLite DBs are removed automatically by tests. No production publisher, database, secret, schedule, runtime or recovery changed.

## Follow-up gates
- SEC-02 and ISO-06 need real least-privilege provider identities, Environment and scoped secrets; do not bypass tool safety denial. 
- Neon owner with ALTER ROLE authority (or provider principal that provisions true NOBYPASSRLS) is necessary to close ISO-04. The Neon API create_postgres_role cannot be trusted to provision least-privilege until verified.
- The final item 10 status must be based on actual GitHub-hosted QA run and unchanged PR SHA, not local tests alone.
