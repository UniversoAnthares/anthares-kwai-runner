# Lease — RET-01 política estável de retenção e quadro fixo
STATUS: RUNNING
AREA: CORTES-retention-policy-readonly
DATE: 2026-10-26
OWNER: ChatGPT
JOB: RET-01-POLICY-FREEZE-20261026
MAX_LEASE: 30 minutes
BASELINE: governance f6fc9ca59a96e451; anthares-clipper/main db6c12fdaa0af01e3b68b8a527b2e02c12c21837
TARGET: anthares-clipper/qa/f1-onecopy-retention-review-20261026 (PR #210), additions only.

SCOPE: establish immutable RET-01...RET-09 identifiers with fixed descriptions; add a machine-readable policy and offline validator/tests. No production deployment. Respect publication confirmations, CORTES cycle policy, F1 2x master/keep-local currently in production, and strict proven Anthares uploader provenance for Google Drive cleanup.

PREFLIGHT: Windows policy.py preflight RET-01-POLICY-FREEZE-20261026 PASS, hashes REGRAS/INDICE/PROMPT all match manifesto. GitHub destination and GitLab peer branch checked; branch exists only on GitHub; untouched new paths verified missing.

SUCCESS: configuration and stable tracker added to PR #210; syntax/schema/negative unit tests run; readback confirms commit; closure finding append-only.

FAILURE: concurrent lease/branch change, failures of tests or git compare, attempts to delete/upload/migrate originals, secrets, automatic cleanup or change F1 runtime. Fail closed on missing receipts. No retry of prior refused file transfers; no tools bypass.

TEST_VALIDITY: offline contract tests do not prove actual upload, deletion, hash restore, or deployment. Enable flag remains false.
