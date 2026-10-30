# LEASE — ARA HTTP 402 -> queue-only recovery
STATUS: RUNNING
AREA: queue / ara-http-selector / C8 SYSTEM
OWNER: current ChatGPT operation, user-authorized repair
START: 2026-10-30 morning America/Campo_Grande
EXPIRY: 30 minutes after this lease commit; release upon completion
BASELINE: Vercel lucasyahn-6808 free team paused at 108% Fluid Active CPU, resumes 2026-11-29. Both primary/secondary return HTTP 402 X-Vercel-Error DEPLOYMENT_DISABLED. C8 SHA256 4FFEFC590D6825BA946373DBDC31F8D61C0B07932807F0C606A2275471FD609C / commit ab6c668; Windows recovery state single-writer-healthy; GitHub/GitLab private queues configured. GitHub main a5bd33a40aa0aee8ea4e1d2021a4be9aa9adc814.
SCOPE: Change only ara-http-selector.ps1 to return empty origin when both controllers are unavailable, preserving issue queues and avoiding Vercel 402 restart storm. Apply guarded Windows hotfix with lastgood integrity copy and rollback. No forced process kill, no HTTP job retries, no Vercel billing changes, no new credentials.
ACCEPTANCE: Code parsing passes; selector returns empty origin upon both HTTP failures and retains primary/secondary when reachable; C8 eventually reports issue-queue-only mode with one SYSTEM process, recovery queues enabled; preserve WAF and Hostinger settings.
ROLLBACK: Restore pre-patch selector and .lastgood from the matching verified backup if runtime regression.
BLOCKERS: If active prior lease or baseline drift found, stop and record.
