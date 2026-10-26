# RET-CI-209 / F1 one-copy review — consolidated closure
STATUS: PARTIAL
AREA: retention
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40395690926
JOB: RET-CI-209-20261026; RET-CI-209-GITLAB-ISOLATED-20261026
COMMIT: GitHub PR209 0139b0978872535fabd0c9b761a0f1fa883c2fb0; GitLab QA 10b9fdcd801acf906ea1733c095de4ae4b553c8b; GitHub F1 PR210 c01b89e0a176991cb0218efb163be1c1d620708b
SUPERSEDES: none

## Results
1. Added `.github/workflows/cortes-retention-readonly-qa.yml` on PR209, with read-only contents permission, PR number 209 gate, no secrets, Python syntax and synthetic unittest. GitHub Actions run 40395690926, job 121827983246: completed FAILURE, **steps=[]**. The job did not execute tests. An unrelated YouTube validation on PR209 run 40395690800 completed SUCCESS and does not count as retention CI.
2. Independent GitLab QA-only branch `qa/retention-209-ci-isolated-20261026` created atomically from GitLab main with isolated `.gitlab-ci.yml` (one job, no publish/mirror). Three QA sources were read from GitHub PR209 and GitLab blob IDs exactly match their GitHub blob SHAs: df21da0743fb86e05d9bba902efc8dae697017ea, cb6f5edaceac2ee4d2c0dcc34513a3f6e69062ff, ec156ff68f76cae6511573f9c3db8629f3620c03. Pipeline 2991595931 and job 17483410721 FAILED with **ci_quota_exceeded**, not a code test. Do not repeat while quota unchanged or buy a plan.
3. Anthares Remote PowerShell preflight PASS job RET-CI-209-20261026, governance version f6fc9ca59a96e451. Read-only Windows inspection located genuine F1 historical local ledger `C:\ProgramData\AntharesCortes\gdrive\f1-real-20261024\state\real-master-ledger.json`: master `output/yt_9CIk-I_3VhM_8_98.mp4`, bytes=12,002,478, sha256=4ce5255d655d2017615bed36309008d8632d2e007b8fc8e361430516017eb49b, remotes cortes_drive_profile3 and profile9 with verified=true dated 2026-10-24. Synthetic ledgers separately identified. Current runner-media/state/google-drive-replicas.json NOT FOUND in observed listing and current F1 status was idle_no_eligible_media.
4. `D:\AntharsWork\cortes-facebook-long-20261020\uploaded_02.json`, `uploaded_03.json`, `uploaded_04.json` contain only index, attachment_id and UTC, consistent with publication attachment receipts. Facebook manifest is 3 video build rows. No verified Drive fileId/upload ledger receipts for the 14 archived Facebook objects found in the scoped sources. All 14 remain HOLD; NO deletion authorization.
5. Separate GitHub DRAFT PR210 `qa/f1-onecopy-retention-review-20261026` adds pure review assessor, 21 local synthetic QA tests and contract document. Three additions; no F1 guard/runtime, cron, producer, profile, queue, or published content changed. Exact hosted CI for PR210 is NOT verified.
6. Existing Windows self-hosted runners observed: C:\actions-runner registers with anthares-clipper and had active Runner.Worker; independent QA runner registers with anthares-kwai-runner, not clipper. Do not redirect CI onto shared/active publication runner or cross-project QA runner without coordination, guard and capacity proof.

## Restrictions and follow-up
- RET-02 synthetic code in GitHub PR209 remains DRAFT and CI_NOT_TESTED despite local 52 tests PASS.
- RET-04 historical F1 receipts FOUND (not the archived Facebook provenance). Need exact Drive fileId and verified upload provenance for Facebook objects.
- RET-05 review prepared as GitHub PR210 DRAFT; current F1 2x + local original remains unchanged.
- RET-06 original explicit security denial for Drive uploads remains unmodified; no alternate-channel replay.
- RET-07/08 no deployment, retention timer, deletion, upload or restore performed.
- RET-09 Test Hub finding append-only in PR1459 branch, pending canonical review/merge.
- CI remediation requires legitimate available runner/zero-cost quota restoration or administrative GitHub CI/billing resolution. Never label a pipeline success if steps were absent or the CI quota was exceeded.
- Leases `20261026-ret-ci209-f1-review-lease.md` and `20261026-ret-ci209-gitlab-isolated-lease.md` are CLOSED by this finding. No long-lived owner lock.
