# Asaas webhook regression acceptance and provider discovery safety
STATUS: PARTIAL
AREA: wordpress-payments
DATE: 2026-10-08
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927095972
JOB: 17035253768
COMMIT: 65ce499fbf875b8aa77220e31407b57060b97f9c
SUPERSEDES: 20261008-lease-asaas-functional-regression-qa.md

Hosted GitLab PHP 8.5 job trace reports `PASS existing`, `PASS corrupt`, `PASS decrypt-fail`, `PASS encrypt-fail`, `PASS write-fail`, `PASS new-token`, `ASAAS_WEBHOOK_TOKEN_REGRESSION=PROVEN`, `GITLAB_WORDPRESS_QA=PROVEN`, and `Job succeeded`. These tests exercise the real extracted PHP token function with isolated WordPress mocks and check absence of destructive deletion in source; not a live Asaas provider acceptance test.

Further review exposed an ambiguity in PR18: finding an existing provider webhook with same URL does not prove its authToken matches local secret, so marking its ID as locally configured would conceal mismatches. Follow-up commit `d71a3490b5ab7bcbdee792e2f52bfb6eb95404fb` on the same PR branch removes that false association and fails closed if GET /webhooks fails. GitLab follow-up pipeline https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927111773 job 17035374009 was RUNNING at last check. Do not claim follow-up CI success until evidence. Both commits are mirrored to GitLab branch. No production deployment or financial operation.

Cloudflare read-only /health returned ok=true, provider=cloudflare, persistent_state=true, queue_bound=true, pc_fallback=false, version=2026-10-05-no-pc-confirmation-v12; this is health evidence only, not real publisher acceptance.
