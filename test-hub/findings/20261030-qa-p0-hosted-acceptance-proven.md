# Item 5 — QA-P0 cloud-only production acceptance
STATUS: PROVEN
AREA: architecture/qa-p0
DATE: 2026-10-30
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41056710386
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41056710386/job/124065953316
COMMIT: 86b57961501473549bf445ccd9ec3a2cd12aaa30
SUPERSEDES: lease-20261030-qa-p0-hosted-five-minute.md

## Objective
Remove operational QA-P0 control-plane, bounded executor and authenticated WordPress source monitor from PC. Preserve original P0 incident bounds and independent alerts.

## Results with real evidence
Controller moved via PR #1935: hosted Ubuntu run 40992225120, job 123857093476, SUCCESS and QA_P0_FINGERPRINT_DEDUP=PASS.
Executor moved via PR #1969: hosted Ubuntu run 41054962276, job 124060064690, SUCCESS, issue #622 authorized, 19 policy tests PASS, QA_P0_GITHUB_POLICY_VALIDATED_REPAIR_UNCONFIRMED. Daily local-task wake was replaced by safe DAILY_EXTERNAL_RECOVERY_REQUIRED_NO_LOCAL_WAKE, without claiming source repair.
WordPress authenticated canary: PR #1970 hosted run 41055582795, job 124062159189, SUCCESS; 8 offline tests PASS; CORTES_WP_AUTH_SMOKE=AUTHENTICATED_JSON_ITEMS_155. Prior 2MB size gate corrected to bounded 16MiB, matching existing trusted SSH limit.
Production watchdog: PR #1970 and PR #1972, hosted Ubuntu run 41055843075 and run 41056710386, route job 124065953316 and alert job 124065953584 both SUCCESS. ROUTER_OK observations=2 opened=0 sources_failed=0; github=1, daily-round=1, wordpress=0 observations; cloud alert PASS candidates=0. No media dispatch or closure was performed.
GitHub main schedule configured for five-minute hosted router (*/5) and separate existing twice-hourly cloud-alert (13,43); filters prevent duplicate scheduled jobs. Preserve old serial QA route concurrency lock to avoid overlapping queues. First invocation of new scheduled cron remains to be observed separately; verified main push integration proves runtime.
Local task inventory: WinRemote TaskList by exact old QA-P0 SYSTEM task name, P0, QA and Anthares reported no matching old QA-P0 scheduled task, while unrelated Pinterest QA appears. Do not remove unrelated tasks, local runners or publishers.

## Safety and consequence
QA-P0 source scan and issue controller/executor are hosted and authenticated with least-privilege WordPress QA secrets; P0 diagnostics never assert publication repair. WordPress 401/403 must fail closed, preserve separate real incidents. Other item scopes (daily producer, media preservation, local runners, GitLab quota, Instagram publishing) remain independent.
