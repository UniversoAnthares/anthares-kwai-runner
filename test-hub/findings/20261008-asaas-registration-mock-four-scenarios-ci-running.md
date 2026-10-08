# Asaas registration function isolated acceptance
STATUS: PARTIAL
AREA: wordpress-payments
DATE: 2026-10-08
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927154498
JOB: 17035719786
COMMIT: b7e36126744273a133342e169a0139a0a19cd2e2
SUPERSEDES: 20261008-lease-asaas-webhook-registration-fixtures-round2.md

Added `tests/test-asaas-webhook-registration.php` to WordPress PR18, extracting the actual registration function into isolated PHP with mock provider and WordPress functions. Four scenarios: empty local token makes zero provider calls; provider GET error never triggers POST; existing same-URL webhook is preserved with no POST or DELETE; no existing webhook triggers GET then POST. The GitLab PHP CI now invokes this file after six earlier token regressions. GitHub/GitLab PR branch mirrored at SHA b7e36126744273a133342e169a0139a0a19cd2e2. GitLab pipeline 2927154498 was RUNNING at last observation; no claim of test pass yet. All tests are mock based, no Asaas production network calls or payments.

Independent hosted status: Clipper GitLab main pipeline 2926810017 SUCCESS, Kwai GitLab main pipeline 2927124668 SUCCESS; neither proves live social publishing.
