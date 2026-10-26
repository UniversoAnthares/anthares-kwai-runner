# CF-02 item 19 — production receipt REAL historical recovery under protected main
STATUS: PROVEN
AREA: github,cloudflare
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40283336472
JOB: 121441273566
COMMIT: 992651f0069d27b84231834a28b711dc4ccc9c53
SUPERSEDES: test-hub/findings/20261026-cf02-prod-receipt-recovery-running.md; test-hub/findings/20261026-cf02-recovery-log-auth-running.md; test-hub/findings/20261026-cf02-attested-prod-receipt-pr-running.md
LEASE_AREA: cf02-production-receipt-recovery-no-deploy
LEASE_OWNER: ChatGPT-CF02
LEASE_STATUS: CLOSED

## Resultado
- Original acceptance CF02 item 19 staging one Worker rollback R07.6 remains DONE: real health200, 503 fault and rollback 200, with production isolation per PR #1402.
- Historical PRODUCTION deploy run #40283336472/job #121441273566 source HEAD 26ae1bdb3ba1095ab8b0230893134053804b4709 verified via actual GH Actions steps and timestamped logs: WRANGLER_DEPLOY_OK=1, CORTES_LEGACY_CLEANUP_REMOVED=0, CORTES_LEGACY_CLEANUP_PROTECTED=6, CONTROL_HEALTH_OK=1, TikTok endpoint unauth boundary SUCCESS; only original receipt PUT failed HTTP409. Overall run conclusion FAILURE is not concealed.
- Github provider CAS fix merged #1346 main SHA 00634f8, real provider QA #40319550329 SUCCESS. Dedicated non-deploying recovery workflow #1448 and safe redirect fix #1450 integrated; latest run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40329764097 confirmed original run/jobs/logs and live health but got HTTP409 on its final direct main PUT.
- Root cause confirmed GitHub ruleset proteger-main #25443611 ACTIVE requiring pull_request; no main protection weakening. Normal PR https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1451 MERGED by squash commit 992651f0069d27b84231834a28b711dc4ccc9c53 [skip ci] to avoid unrelated workflows.
- Independent GitHub fetch MAIN after merge confirmed production receipt path .github/cloudflare-cortes-status.json blob fe8b546ea7df413de6ad4da39383291aef38474a (changed from 47faf493a965be52cf57ea8780cc61f68510567f) with checked_at_utc=2026-10-26T13:23:51.5719939Z; deploy_outcome=success; control_version=2026-10-17-physical-android-v18; control_healthy=true; cleanup_outcome=success; removed_count=0; receipt_mode=verified_historical_recovery; source_workflow_run_id=40283336472, source job id 121441273566; cloudflare_deploy_in_recovery=false; queue_mutation_in_recovery=false; current_queue_states_verified=false. Current live health proof at 2026-10-26T13:23:51.244Z was true and bound.
- Governed Windows preflight ARA CF02-RECEIPT-VALIDATION-20261026 exit0; governance current GitHub manifest 2e28d54043d6bad1 vs Windows local f6fc9ca59a96e451 diverged, preserved without overwrite. Google Doc canonical checklist https://docs.google.com/document/d/1SkjpRPJYLe9n_9SDOA4s-RibN8Pb_hm6-ukS6pbV7aQ/edit updated with receipt recovered and the limits; readback confirmed.

## Limites e proteção
This PROVEN receipt is a RECOVERY from true historical production deployment, not a new Cloudflare deploy E2E with new receipt written by original deploy job. No new Worker deployment, queue cleanup, social publish, token transfer, or permission relaxation was performed to recover it. Rule proteger-main requires future productive workflow receipt writes to use reviewed PRs rather than direct Contents PUT; opening an independent follow-up to update the original deployment workflow is safe and does not reopen one-Worker stage item 19 acceptance.
No TEST HUB lease remains open for this recovery. Other CF02 Workers are a separate scope.
