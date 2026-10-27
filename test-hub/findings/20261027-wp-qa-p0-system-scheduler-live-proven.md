# WordPress QA P0 — original Windows SYSTEM schedule live PROVEN
STATUS: PROVEN
AREA: wordpress-qa-auth
DATE: 2026-10-27
SUPERSEDES: 20261027-lease-wp-qa-scheduled-system-live-chatgpt.md
SOURCE_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1720
SOURCE_COMMIT: 9f0d2afbc5637121d2ac5b8750b126587ded2fc6

## Real original scheduled-job result
- Windows: DESKTOP-FTDK0HP, existing task `Anthares CORTES P0 QA Immediate Independent`, effective principal `NT AUTHORITY\\SYSTEM` (SID S-1-5-18).
- Original scheduled task previously returned result 2 and logged `CORTES_QA_SCAN_FAILED source=wordpress code=AUTH_MISSING` each 5-minute interval.
- Source correction merged in PR #1720; SHA-pinned 28/28 Python regressions passed and actual SYSTEM SSH WordPress data read verified.
- Under the existing task, 2026-10-27 19:36 and 19:38 America/Campo_Grande: `CORTES_QA_SCAN source=wordpress observations=0`, `CORTES_QA_ROUTER_OK observations=46 opened=0 sources_failed=0`, `P0_QA_ROUTER_COMPLETED`, and Task Scheduler `LastTaskResult=0`.
- After exact-contents digest resilience enhancement, manual invocation of the same authorized task at 19:40 registered the same three signals and Task Scheduler `LastTaskResult=0`. No new schedules, credential copies, posts or altered publisher behavior.

## Safe provenance and recovery
The Codeberg main source still matched the known earlier GitHub main revision, and GitHub-to-Codeberg hosted mirror pushes failed with `info/refs not valid` on multiple attempts. The original Windows wrapper was syntax-validated and atomically replaced with a backup. Its bounded fallback applies only when Codeberg's downloaded QA source is exactly SHA-256 `BBDA943AB8706D4FED161DBDB4797B1AA2C3B69578CF74B94768AF4822521F48` and lacks the new SYSTEM guard. It then downloads current canonical GitHub source, validates the existing QA marker and new guard, checks Python syntax, and runs under existing SYSTEM identity. When Codeberg advances with the new source, its prior primary loading path is retained. Preserve the original task mutex and five-minute cadence.

## Scope
WordPress authenticated read-only production-data QA scanning is PROVEN on the authorized Windows SYSTEM task and on the named GitHub Actions QA runner. Separate Application Password REST GitHub secrets remain unprovisioned; they are unnecessary for the authorized SSH read-only fallback. GitHub-to-Codeberg general repository mirror health remains an independent issue; a healthy local QA task is not evidence that repository pushes are repaired.

## Evidence
GitHub PR #1720 and its post-merge real-operation comment; Anthares Remote verified live task result 0 and exact scanner lines at 2026-10-27 19:36, 19:38 and 19:40 local time.
