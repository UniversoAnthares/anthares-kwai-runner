# Test Hub — CORTES cloud media double-pass checkpoint
STATUS: PARTIAL
AREA: architecture
OWNER: ChatGPT
DATE_LOCAL: 2026-10-23
JOB: cortes-cloud-migration-double-pass-20261023
BASE_REF: anthares-clipper/feature/cortes-cloud-drive-replication-20261023
TESTED_HEAD: 383d38ed3cb2315917b546db6e6c49c7e8c9f7bd
GOVERNANCE_VERSION: 898630c1c5143f34

## Exact proof results
1. Northflank read-only API authentication confirmed. Project default has active YouTube Shorts backup job and 2 existing services. Billing credit-balance available=0 USD; no new resource, job, build or billed media task launched.
2. Real local ffmpeg+ffprobe canary successfully rendered temporary synthetic long: 332s, audio true, one microcut, 1,572,499 bytes, SHA c5ce745fa6767a5bce399c23a3587854009563bb9e5074a88286d30610168d54; unchanged source; own temp directory cleaned. Does not prove cloud.
3. Neon QA branch br-silent-mud-b8fzvqta: 003 delivery ledger per master+platform+account and 100 first-start cap. One Kwai account at 100 blocked 101st, other Kwai account unblocked; owner/generation rejected when stale. 004 media gate: claim denied absent two replica proofs; synthetic verified replicas allowed exact hash and short platform; wrong stage/hash denied; revoked second replica blocks later start. No Neon main migration.
4. F7: local retention apply now requires authoritative production ledger reconciler; CLI no callback blocks. New provisional read-only finalization report never issues delete proof.
5. Google Drive read-only quota: profile9 once returned 14.95/15GiB free, subsequent capacity gate rejected all three profiles; no writes attempted. Prior dedicated OAuth blocker remains. Replica guards require fresh free space and 512MiB reserve; >=25GiB source cannot fit in a 15GiB account.
6. F3 planning for bounded source shards: 10-minute intervals with 2-second overlap, up to 24h/144 shards, no full source download. Not yet connected to real media origin.
7. Staging QA ran 169 tests, 168 passed, 0 failed, 0 errors, 1 symlink skip. GitHub Actions/CI quota not used. All live social publishers, cron, desktop data, production Neon and existing Northflank services untouched.

## Remaining gates
Authenticate two dedicated Drive OAuth accounts with actual binary upload/readback SHA. Source bounded ingestion/download implementation; real Whisper/transcription and two-person video render on cloud with quota. Two independent external compute backups; GitLab quota previously exhausted, Codeberg/Forgejo not yet verified. Canonical social ledger reconciliation and two-Drive live readback before any GC. PC-off/dual-failover E2E and controlled promotion.

## Durable references
PR draft: https://github.com/UniversoAnthares/anthares-clipper/pull/190
Google Doc sections 20–21: https://docs.google.com/document/d/1ZXsdBv4JKFlmRx3fDb4Twpr33u_Ht1hsQFRWGdw0ajo/edit
Governance: https://github.com/UniversoAnthares/anthares-governance/blob/main/PLANOS/CORTES-MIGRACAO-CLOUD-2026-10-23.md

## Rollback / scope
Feature branch only for code; Neon migrations 003–004 only on QA branch. No merges, source-cycle rewrite, platform modifications, credential disclosure, shadow publication, or unauthorized media deletion.
