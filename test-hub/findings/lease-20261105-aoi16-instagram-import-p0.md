# AOI #16 — lease de correção de import Python Instagram
STATUS: RUNNING
AREA: qa-p0-instagram-import-failure-41258536427
DATE_UTC: 2026-11-05T01:22:32.797Z
EXPIRES_UTC: 2026-11-05T01:52:32.797Z
OWNER: chatgpt-aoi16-20261105
BASE_HEAD: bd6610036568a4f4399b4d621e64f3d05800f961
ITEMS: [16]
SOURCE_BLOB: scripts/instagram_autopublish.py 0c675d1fb4754b0df6e0a76d32f93ee9fc0e6a93
TEST_BLOB: test-hub/test_instagram_autopublish.py 5ad4605c8a550d7719b5b5d9ed12265e6fd0b657
PEER_BLOBS: GitLab project 87307248 main mirrors both target blobs exactly
BASELINE_PROVEN: run 41258536427 / job 124706765819 failed in inline package import 'from scripts.instagram_autopublish import load_ledger, save_ledger' with ModuleNotFoundError: No module named 'instagram_publish'. Root cause is scripts/instagram_autopublish.py's top-level 'from instagram_publish import ...' instead of the importable package path. GitHub workflow instagram-auto-10day.yml is disabled_manually.
FAILED_AVOIDED: no GitHub Actions dispatch, no media fetch/processing, no API publishing, no ledger mutation, no reactivation, no PC filesystem work, no paid quota.
SUCCESS_SIGNAL: exact package import from repo root works in isolated interpreter; existing unit contracts pass; source only changes the import and adds regression.
FAILURE_SIGNAL: import still fails, unexpected imports/side effects, workflow state changes, or identity/quota guards weakened.
TEST_VALIDITY: offline Python import and unit regressions; no claim of live publishing repair until separately proven on hosted runner and remote platform.
SCOPE: only scripts/instagram_autopublish.py, test-hub/test_instagram_autopublish.py, Test Hub findings, no other existing workflow.
