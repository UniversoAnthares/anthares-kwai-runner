# GitLab QA-only jobs routed to free Render; hibernation wake recovery
STATUS: PARTIAL
AREA: gitlab-qa
DATE: 2026-10-10
RUNNER: https://anthares-gitlab-qa-runner.onrender.com/
MR: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/merge_requests/34
BRANCH: qa/render-runner-migration-20261010
COMMIT: c26c4afd748a0bc1b1373e6c90f396e1647aa18a
PIPELINE: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2934499529

## Proven
- Protected QA branch CI committed with six QA-only jobs changed from `tags: []` to `tags: [render-qa]`, no changes to main branch.
- Initial pipeline 2934461770: redundancy probe and WordPress security sniffs succeeded, then PHP compatibility job became orphaned at Git fetch after Render hibernation; canceled pipeline (GitLab still canceling at 19:46Z).
- New free GitHub Actions keepawake workflow `.github/workflows/render-gitlab-qa-free-keepawake.yml` pings Render every five minutes. Run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38080865722 succeeded; Render HTTP 200 `connected` independently confirmed.
- Fresh pipeline 2934499529 running; redundancy probe success and security sniffs executing on custom runner.
- Actual PHP 8.5 image already proven on custom runner in GitLab job 17085304601. No paid runner or local PC.

## Not yet proven
- Seven-job new pipeline green, JS/fast PHP/compatibility checks and full WordPress QA.
- Render Free may still hibernate if scheduled GitHub pings are delayed; monitor with fail-closed logic, do not claim uninterrupted always-on operation.
- MR !34 remains Draft, do not merge before all required QA is green.
