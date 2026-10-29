# Lease: migrate TikTok @lucasrosalem4 manifest validation to hosted GitHub/Neon
STATUS: RUNNING
AREA: tiktok-secondary-manifest-offload
DATE: 2026-10-29
JOB: item6-fixed-list-no-pc
COMMIT: 9e2071ec6a80d573f489a36db7d534aa5011c285
SUPERSEDES: none
LEASE_OWNER: chatgpt-item6-lucas4-20261029
LEASE_EXPIRES_UTC: 2026-10-29T18:02:00Z
SCOPE: ONLY tools/cortes_tiktok_lucasrosalem4_manifest.py, tests/test_cortes_tiktok_lucasrosalem4_manifest.py and .github/workflows/cortes-tiktok-lucasrosalem4-manifest.yml.

BASELINE_PROVEN: Existing Neon source-manifest authorized by OIDC reads immutable confirmed clip URLs and today's date from remote database; the GitHub script was materializing redundant local per-account manifest in C:\\Users\\Lucas\\AppData\\Local\\Anthares\\TikTok\\secondary-publisher. Github source search + Windows scheduled actions/git grep found no other programmatic consumer of that local manifest in scoped versioned code. Windows run 40907673633 did not pass actions/setup-python@v5. Existing verified GitHub-hosted Ubuntu runs in same public repo.
FAILED_AVOIDED: Do not rerun Windows preparation or rewrite live publisher queues, local media or credentials. External read and validation only; no publishing, enqueue, duplicate effects or deletion. OIDC must remain pinned to refs/heads/main and existing workflow allowlist. No quota fallback to GitLab until independently available; recent pipelines failed ci_quota_exceeded.
SUCCESS_SIGNAL: hosted Ubuntu runner executes Python unit tests and, on main, obtains signed OIDC source-manifest response from canonical Neon with account/day/count/clip validation; prints SECONDARY_TIKTOK_NEON_SOURCE_VERIFIED and never writes a local account manifest.
FAILURE_SIGNAL: proof of an active consumer of local manifest, auth failure, missing remote state or data validation failure, quota exhaustion, or runner nonallocation.
TEST_VALIDITY: no steps/runner => NOT_TESTED; PR branch manual run validates code only because Neon enforces main branch; main run required for actual signed GET proof. No publishing tests.
GOVERNANCE: REGRAS SHA256 CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138; INDICE SHA256 2EFAB2052ABDD9083FAB5DA6E489846E0AA75C7A8097C576AAE5D0BDE0A69D12. GitLab main paths read before mutation; PR not mirrored blindly.
