# Test Hub final R3 — media shards, fallback and quotas
STATUS: PARTIAL — safe staging checkpoint
OWNER: ChatGPT
AREA: CORTES cloud media producer architecture
DATE_LOCAL: 2026-10-23 / America/Campo_Grande
JOB: cortes-cloud-r3-20261023
GOVERNANCE_VERSION: 898630c1c5143f34
TARGET_BRANCH: UniversoAnthares/anthares-clipper feature/cortes-cloud-drive-replication-20261023
TESTED_BASE_HEAD: 0589d18f9c856922698c77042938baa0e7228ff3
CODE_DOC_COMMIT: 1165b6f95fd71feb6d2b6d8ae9ac19a72bccb051
GUARDRAIL: staging only, no social publisher edits, GitHub Actions disabled, no production writes

## Proven locally with actual video/audio bytes
- FFmpeg MP4 shard from SHA+cycle locked source with active lease before and after, write atomic timeline/SHA receipt, replay rejects overwrites.
- Shard WAV audio extraction -> synthetic transcription fixture -> per-shard checkpoint -> SHA-bound aggregation with model/source/day/time anti-mixing. Source immutability and temporary-file cleanup verified in 21 targeted offline tests.
- Real synthetic 12s FFmpeg shard + actual WAV, no real Whisper inference, no external source fetch. Real synthetic Short 45s/720x1280/audio/one microcut/single fullframe, no fake two-presenter proof.
- Full locally-executed synthetic producer E2E: canonical source hash -> MP4 shard real -> WAV real -> synthetic words -> aggregate -> exhaustive recognized-speech coverage -> Short real 42s/720x1280/audio/one microcut. SHA of short a919dbb2cab16eca340d2d4090777ae1beae3e3c293b2508fa7f3b2a6df0a75c. Own QA temp auto-removed.
- Consolidated tools/cortes_cloud_qa.py: tests_run=192, passed=191, errors=0, failures=0, skipped=1 (Windows symlink).
- Linux transcribe Dockerfile staged with new FFmpeg shard ingester/transcription/merge modules, default probe and no publisher modules. No hosted build.

## Proven in actual Neon QA transactions (not production)
- Staging migration 005: America/Campo_Grande local day must equal today on start, YouTube long quota 3/account/day (4th rejected), Facebook and other long 10 (11th rejected), short 100 under existing safeguards.
- QA synthetic job 623f637e-b47b-48f6-a2a1-fdb5e6b17a20: owner gen1 expired -> uncertain -> explicitly reconciled in isolated QA -> gen2 new owner accepted; gen1 unable to finish even after new owner claimed. NOT real external failover.
- QA executor_proofs northflank unknown, GitLab quota_exceeded, Codeberg/Forgejo media unknown, Windows local only. Cannot promote.

## External discovery and owner-action blockers
- Codeberg main SHA a775b3ee32023732a9107633fba139e32f68b026 matched GitHub main. 12 hosted Codeberg Actions success for existing CI/admission, including codeberg-tiny. This proves remote CI, NOT media FFmpeg/Whisper.
- New read-only Codeberg media staging QA workflow exists ONLY in GitHub feature .forgejo/workflows/cortes-cloud-media-qa.yml; attempted push feature to Codeberg returned remote: Forbidden. Stop, no rerun via alternate credentials/browser/API. Owner must authorize Codeberg write role first. No Codeberg feature branch created.
- Northflank API active authenticated; two most recent Shorts job runs FAILED while earlier SUCCESS; sanitized logs show RuntimeError in cortes_shorts_cloud_entrypoint.py and cortes_youtube_shorts_cloud.py. No existing job changed; no hosted media build. Credit balance available=US$0 and free compute unverified.
- GitLab CI quota exceeded, Forgejo compute unknown. Two physically independent media backups still missing.
- Two dedicated Google Drive OAuth remotes and actual binary SHA readbacks still missing, no uploads; Windows cleanup guarded off.

## Documentation & rollback
- Google Docs sections 23–24 added: https://docs.google.com/document/d/1ZXsdBv4JKFlmRx3fDb4Twpr33u_Ht1hsQFRWGdw0ajo/edit
- Private governance plan R3 checkpoint added https://github.com/UniversoAnthares/anthares-governance/blob/main/PLANOS/CORTES-MIGRACAO-CLOUD-2026-10-23.md
- PR draft #190, no merge to main.
- No user media deletion, live posting, production Neon DDL, platform token exposure, paid build, Docker cloud job or GH Actions execution.

## Next
1. Codeberg provider-approved role to push branch (do not bypass denied write); run hosted media-only test if approved.
2. OAuth dedicated 2 of 3 Drive remotes and real SHA readback canary / capacities.
3. Real source-incremental download adapter and real faster-whisper inference in external executor with zero-cost plan confirmed.
4. At least 3 independent media compute hosts total, fencing/heartbeat/full failover and PC-off scenario.
5. Canonical social ledger account reconciling, platform proof, and dry-run/controlled Windows+cloud cleanup.
