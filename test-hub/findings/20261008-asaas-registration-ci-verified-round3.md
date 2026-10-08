# Asaas webhook registration CI verification
STATUS: PROVEN
AREA: wordpress-payments
DATE: 2026-10-08
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927154498
JOB: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/jobs/17035719786
COMMIT: b7e36126744273a133342e169a0139a0a19cd2e2
SUPERSEDES: 20261008-lease-asaas-webhook-registration-fixtures-round2.md

## Scope
Hosted isolated PHP fixture tests, no provider network, no live payment or webhook registration.

## Decisive evidence
Job trace contains PASS empty-token, PASS list-error, PASS existing-webhook, PASS create-new, ASAAS_WEBHOOK_REGISTRATION_REGRESSION=PROVEN, six token fixture PASS lines, ASAAS_WEBHOOK_TOKEN_REGRESSION=PROVEN and GITLAB_WORDPRESS_QA=PROVEN; job status success.

## Follow-up risk
Current get_transient/set_transient lock is not atomic and is shared across environments; concurrent registration may race. The tests mock transient as always absent and do not prove concurrent exclusion. Existing webhook preservation requires manual reconciliation when provider token cannot be verified. No production deployment authorized by this finding.
