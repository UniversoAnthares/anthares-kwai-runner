# Asaas webhook stale-lock CI verification — 2026-10-08

Status: PROVEN (isolated CI); production integration NOT PROVEN.

GitHub branch: UniversoAnthares/anthares-wordpress `fix/asaas-webhook-failclosed-20261008`.
GitLab synchronized commit: `dc127252feea36fdb9db9a43e383d3031f79d38c`.
Pipeline: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927362462
Job: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/jobs/17037368048

Evidence: PHP lint succeeded; 6 token fixtures and 11 webhook registration fixtures passed, including `stale-lock`; log includes `ASAAS_WEBHOOK_TOKEN_REGRESSION=PROVEN`, `ASAAS_WEBHOOK_REGISTRATION_REGRESSION=PROVEN`, `GITLAB_WORDPRESS_QA=PROVEN`, `Job succeeded`.

Safety: registration lock uses atomic `add_option` and per-environment key; stale locks fail closed instead of unsafe deletion. Trade-off: orphaned lock requires explicit, controlled reconciliation. Existing provider webhook requires reconciliation because auth token cannot be read back. No merge or production deployment performed. Do not label live Asaas webhook delivery PROVEN from isolated CI.
