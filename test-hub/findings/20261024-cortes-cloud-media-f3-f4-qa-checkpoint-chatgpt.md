# Test Hub — CORTES cloud-media F3/F4 QA checkpoint
STATUS: PARTIAL
AREA: architecture
DATE_LOCAL: 2026-10-23
JOB: ChatGPT/cortes-cloud-media-f3-staging-20261023
OWNER: ChatGPT
BASE_REF: anthares-clipper/feature/cortes-cloud-drive-replication-20261023
TESTED_HEAD: 809911969884b9d0414957148772192513363df8
POLICY_VERSION: 898630c1c5143f34

## Proven
- Preflight policy.py under Anthares Remote returned success.
- Peer GitLab mirror has no corresponding feature branch; no force sync.
- New isolated F3 transcribe worker: 10-minute bounded audio chunks with 2s overlap, ownership/lease check, hash-bound checkpoints and immutable source. Offline model fixtures only, no external model deployment.
- Exhaustive recognized-transcript coverage and fenced segmentation plan without hard 100-master ceiling, no subjective scoring. F4 pure FFmpeg producer core does not import platform publisher modules. Both short (30–90s) and long (5–14min) classes now validated with mandatory microcut evidence.
- Linux images staged only; explicit COPY avoids publisher modules. 25GiB explicit input bound replacing 768MiB.
- Staging QA command: py -3 tools/cortes_cloud_qa.py
- Actual output: tests_run=125, passed=124, failures=0, errors=0, skipped=1 (Windows symlink restriction). GitHub Actions not executed; no social postings or removals.
- PR draft #190, branch has not been merged. Google Docs section 19 updated.

## NOT Proven / do not promote
- No two independent dedicated Google Drive OAuth credentials in rclone yet; no real upload or SHA readback across remotes.
- No real Northflank Docker image build/transcription/render, quota guarantee, or configured whisper model volume.
- No two independently hosted external backup executors for every media stage; GitLab previously ci_quota_exceeded.
- Neon SQL/functions only QA, controller lacks production secret/wiring. No live publication/retention reconciliation.
- No PC-off E2E failover. Windows remains existing live path; no cleanup apply.

## Next
Credential provisioning and probe/canary on two Google Drives; Northflank staging image build and long-source canary; alternative Codeberg/Forgejo/GitLab executor verification; Neon heartbeat and stage contracts; publication isolation; verified retention. Do not blindly retry uncertain jobs.
