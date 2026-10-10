# Lease: GitLab custom runner isolated image probe retry
STATUS: RUNNING
AREA: gitlab-qa
DATE: 2026-10-10
OWNER: chatgpt-kwai-gitlab-followup-1921Z
LEASE_UNTIL: 2026-10-10T19:27:00Z
BASELINE_PROVEN: GitLab MR !34 branch protected; runner 57276512 online; pipeline 2934134870 shared jobs failed ci_quota_exceeded; custom_php_image_probe 17084427523 canceled externally after udocker exported php:8.5-cli image, before php -v proof.
FAILED_AVOIDED: do not retry entire pipeline or shared jobs; do not edit protected main or merge MR; retry only custom runner image job after previous external cancellation.
SUCCESS_SIGNAL: custom_php_image_probe on render-qa completes with exit 0, actual PHP 8.5 image version and ANTHARES_CUSTOM_IMAGE=PROVEN.
FAILURE_SIGNAL: custom job fails or times out; distinguish runner image failure from quota failure.
TEST_VALIDITY: GitLab retry must create a fresh job with same SHA and runner tag; a queued/canceled job is not image proof.
