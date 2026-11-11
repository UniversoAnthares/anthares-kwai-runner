# Lease: CORTES Neon CAS estágio QA
STATUS: RUNNING
AREA: cortes-cloud-producer/ledger-cas-qa
OWNER: chatgpt-cortes-qa-ledger-20261111
START: 2026-11-11T10:15:00Z
EXPIRES: 2026-11-11T10:55:00Z
BASELINE_CLIPPER_HEAD: feeec25bff5ed6a9e6460d551cb161e7933c0078
BASELINE_RUNNER_HEAD: 08b8fd0c657bae66edd838bf8bea0b3f035f89d0
BASELINE_LEDGER_QA_BRANCH: br-silent-mud-b8fzvqta, head rev=1, writer=neondb_owner, epoch=1, QA-only.
SUCCESS: QA-only writer true least privilege, authenticated CAS rejected stale/wrong epoch, independent CI passes; production untouched.
FAILURE: role superuser, invalid function authority, unexpected snapshot state, conflicting agent work, any production mutation.
SCOPE: QA branch Neon only; add safe QA-only code/test coverage on GitHub, validate credentials without disclosing or storing outside intended secret store. No media production, cron, publishing, new storage, desktop processing.
SECURITY: No reset/delete existing roles, no reset of existing owner, no database connection string emitted.
