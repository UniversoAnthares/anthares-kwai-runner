# Lease — TikTok lucas4 IAM/CI shadow admission
STATUS: RUNNING
AREA: account-identity-secret-deploy
DATE: 2026-10-24
JOB: r076-tiktok-lucas4-iam-shadow-20261024
COMMIT: branch platform/cortes-tiktok-lucas4-account-fence-20261024
LEASE_OWNER: ChatGPT authorized owner request
LEASE_SCOPE: create-only ci-hub/cortes_account_iam_audit.py, ci-hub/cortes_tiktok_lucas4_ownership.json, tests/test_cortes_account_iam_audit.py, .github/workflows/cortes-tiktok-lucas4-iam-contract.yml; no existing CI/publisher/secrets/queue/deploy modification.
LEASE_START_UTC: 2026-10-24T22:42:00Z
LEASE_EXPIRY_UTC: 2026-10-24T23:12:00Z
BASELINE_PROVEN: GitHub Actions consumer in separate account @lucasrosalem4; existing workflow reads secret by repository-level reference and does not name account-specific environment; Neon backend validates signed GitHub OIDC by repo, ref and workflow.
FAILED_AVOIDED: static workflow scan cannot certify provider-level IAM; never infer readiness from test green; do not alter or read secret values or interrupt existing publisher.
SUCCESS_SIGNAL: shadow workflow checker refuses secret references for Kwai or generic deploy tokens, wrong account/repository/workflow, missing environment and permissive CI; synthetic named env passes contract but deploy_authorized remains false; package CI runs no secrets.
FAILURE_SIGNAL: foreign secret passes, unverified manifest enables deployment, production workflow changed or external IAM authority claimed.
TEST_VALIDITY: standard-library unit tests plus static contract only; production IAM requires independent source data and real two-principal test.
