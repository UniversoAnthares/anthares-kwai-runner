# Lease — existing-session publisher core
STATUS: RUNNING
AREA: kwai-codespaces-existing-session-publisher
DATE: 2026-10-09
OWNER: chatgpt-existing-session-publisher
LEASE_UNTIL: 2026-10-09T17:02:00Z
HEAD_BASELINE: e4ee785538fdee036e29a3506cee603c1b118b8d
RESOURCES: .devcontainer/kwai-existing-session-publisher.py, tests/test_kwai_existing_session_publisher.py, .github/workflows/kwai-existing-session-publisher-qa.yml
BASELINE_PROVEN: read-only create-surface classifier passed six hosted tests in run 37959630521; bridge/profile files remain owned by a separate active lease.
FAILED_AVOIDED: no Android, no alternate browser/profile, no cookie/storage export, no live publication as audit probe, no mutation of bridge/identity files.
SUCCESS_SIGNAL: hosted QA proves a publisher core is fail-closed unless exact identity and operational create-surface gates are both true, uses only an already supplied page, never launches browser/session state, and exposes separate prepare and final-publish phases.
FAILURE_SIGNAL: core can publish without both gates, launches its own browser/profile, exports session state, or QA fails.
TEST_VALIDITY: offline/synthetic contract QA only. No live upload or publication will be performed in this lease.
