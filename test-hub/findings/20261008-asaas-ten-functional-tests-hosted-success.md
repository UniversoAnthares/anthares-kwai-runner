# Ten isolated Asaas PHP regressions passed in hosted GitLab CI
STATUS: PROVEN
AREA: wordpress-payments-isolated-php
DATE: 2026-10-08
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927154498
JOB: 17035719786
COMMIT: b7e36126744273a133342e169a0139a0a19cd2e2
SUPERSEDES: 20261008-asaas-registration-mock-four-scenarios-ci-running.md

GitLab PHP 8.5 hosted job trace confirms six token regressions PASS (existing, corrupt, decrypt-fail, encrypt-fail, write-fail, new-token), `ASAAS_WEBHOOK_TOKEN_REGRESSION=PROVEN`; four registration regressions PASS (empty-token, list-error, existing-webhook, create-new), `ASAAS_WEBHOOK_REGISTRATION_REGRESSION=PROVEN`; `GITLAB_WORDPRESS_QA=PROVEN`; `Job succeeded`. At last pipeline status poll, pipeline 2927154498 still reported running despite successful job trace. Thus isolated ten PHP regressions and PHP syntax proven, pipeline-wide status must be polled independently. PR18 remains unmerged, no live Asaas calls, no financial operations, no WordPress production deploy. Independent Clipper and Kwai GitLab main pipelines were SUCCESS; no live social post proof.
