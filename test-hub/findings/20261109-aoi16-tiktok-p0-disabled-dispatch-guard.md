# AOI #16 — P0 TikTok: impedir despacho a workflow desativado
STATUS: PARTIAL
AREA: qa-p0-tiktok-recovery-disabled-workflow
DATE: 2026-11-09 UTC
ITEMS: [16]
OWNER: ChatGPT AOI16
SOURCE_RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41085717293
SOURCE_JOB: 124166229307
SOURCE_ISSUE: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/1995
SOURCE_ERROR: HTTP 422 Cannot trigger a workflow_dispatch on a disabled workflow
BASE_GITHUB_HEAD: 5976daa9e0767ba9681a408cf292f102473a17a5
ORIGINAL_BLOB: b75fbef02d4c9c278e349915a6870586dbf0e623
PEER: GitLab public 87307248 main, 7093 bytes identical before edit
SCOPE: .github/workflows/cortes-tiktok-qa-p0-cloud.yml
FIX: consult getWorkflow before listWorkflowRuns/dispatch; when state != active or inaccessible, skip, retain disabled administrative gate and idempotency.
VALIDATION: source readback six static checks PASS, no Actions run or media dispatched.
ACCEPTANCE: candidate source in isolated PR; merge and external readback pending owner/CI review; historical issue #1995 remains open.
ROLLBACK: revert only this workflow commit; do not enable publishers or alter cron.
