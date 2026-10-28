# ARA Event-Driven — item 5 signed reserve Hostinger integration PROVEN
STATUS: PROVEN
AREA: anthares-remote / neon-idle-optimization / signed reserve Vercel controller
DATE: 2026-10-28
RUN: GitHub CI 40781605959 / prior source commit e94cfa127ec26a21a01acaf5295b252448546f78
JOB: Neon ara_reserve_jobs 6bea9055a042721a422b4ac79b3f9a29
COMMIT: e94cfa127ec26a21a01acaf5295b252448546f78
SUPERSEDES: 20261028-ara-item5-reserve-hostinger-lease.md

## Verified production
- Canonical signed gateway cloudflare-ara-mcp routes POST /v1/mcp/execute to anthares-ara-vercel-reserve.vercel.app, standby anthares-ara-vercel-reserve-lucasyahn-6808.vercel.app.
- Vercel project prj_i5ylgY1BgnrPZzSoBZ5UMOtJX77P production deployment dpl_TTrovv6stqw8LyDs7gt3Moe7Jhxb READY; both aliases independently listed as assigned to the same deployment.
- Verified production source archived under vercel-ara-reserve/ in isolated GitHub PR #1817, including signed MCP router, OAuth bootstrap and Neon controller. Only api/mcp.js gained post-INSERT call to Hostinger wake-only sender.
- Feature flag ARA_WAKE_NOTIFY_ENABLED=1, ARA_WAKE_NOTIFY_SECRET Sensitive Production. Hostinger direct origin address in ARA_WAKE_ORIGIN_IP Sensitive Production; HTTPS host/SNI/certificate and bearer still anchored to anthares.us. None of these values are embedded in source.
- GitHub Actions 'ARA reserve Hostinger post-commit notifier' completed SUCCESS at commit e94cfa127ec26a21a01acaf5295b252448546f78.

## Direct live acceptance
- The production Vercel runtime log for dpl_TTrovv6stqw8LyDs7gt3Moe7Jhxb contains authenticated POST /v1/mcp/execute with the positive application evidence 'ara_wake_broker_accepted 52' through 'ara_wake_broker_accepted 71' during 2026-10-28T22:40-22:42Z. These numbers are parsed from Hostinger HTTP 202 JSON receipts; earlier broker sequence was 1, proving fresh signal delivery after deployment.
- Independent Neon read-only query shows job id 6bea9055a042721a422b4ac79b3f9a29 type=file_stat status=done attempts=1 created_at=2026-10-28T22:41:26.387Z.
- GET /healthz 200 and unauthenticated GET /v1/mcp/status 401 confirmed after deployment, with no credential exposure.
- Broker notifications are wake-only signals; the authoritative queue remains Neon and OAuth, signing, leases, idempotency and Windows fallback remain unchanged. This PROVEN record covers item 5 only, not client wake reception, idle SQL elimination or CU-hour savings (items 6,7,10,12).

## Rollback and concurrency
- Original known-good reserve deployment dpl_FmurJGjaAQTfrKAQnEFGFS76TKh3 remains available for Vercel rollback; alternatively turn ARA_WAKE_NOTIFY_ENABLED to 0 and redeploy.
- No GitHub main merge, no Cloudflare Worker change and no change to C8 Windows binary. Separate primary project PR #1815 and Cloudflare wake implementation PR #1808 must not produce duplicate delivery paths during future migration.
