# ARA Event-Driven — item 5: Hostinger wake from canonical signed Vercel reserve — LIVE PASS
STATUS: PASS
AREA: anthares-remote / neon-idle-optimization / anthares-ara-vercel-reserve
DATE: 2026-10-28
JOB: signed Cloudflare MCP /v1/mcp/execute
COMMIT: e94cfa127ec26a21a01acaf5295b252448546f78
SUPERSEDES: 20261028-ara-item5-reserve-hostinger-lease.md

## Verified evidence
- Correct controller: Vercel project prj_i5ylgY1BgnrPZzSoBZ5UMOtJX77P, Cloudflare signed gateway points to https://anthares-ara-vercel-reserve.vercel.app and standby alias.
- Production deployment dpl_TTrovv6stqw8LyDs7gt3Moe7Jhxb is READY. Both aliases anthares-ara-vercel-reserve.vercel.app and anthares-ara-vercel-reserve-lucasyahn-6808.vercel.app are assigned to this exact deployment.
- Deployment files include src/api/mcp.js and src/api/wake-notifier.js. The original queue INSERT remains authoritative, and the wake call is after the resolved INSERT.
- Vercel Production has ARA_WAKE_NOTIFY_SECRET and ARA_WAKE_ORIGIN_IP as sensitive environment variables and ARA_WAKE_NOTIFY_ENABLED as Production config. Values are never logged or checked in.
- The original signed MCP Ed25519 authentication, nonce/replay rules, Neon queue/leases, idempotency and Windows C8 remain in place. Wake is signal-only and fails open.
- GitHub pull request #1817, SHA e94cfa127ec26a21a01acaf5295b252448546f78, workflow ARA reserve Hostinger post-commit notifier COMPLETED SUCCESS.
- Direct production Vercel runtime logs for deployment dpl_TTrovv6stqw8LyDs7gt3Moe7Jhxb show POST /v1/mcp/execute with `ara_wake_broker_accepted 52` through `ara_wake_broker_accepted 59` at 2026-10-28T22:40 UTC. Previous production deploy dpl_3sgJgahpfus97mFXNKtdy9fziRWv had accepted sequence 41-51. Hostinger PHP /ara-notify/index.php?action=signal responds HTTP 202 with `sequence` only after the server file state write; the sequence receipts establish delivery and persistence at the broker.
- Anthares Remote signed session reports device_connected=true. The controlled test command was recorded as done in Neon with one attempt (job fbb8e9d49dbd2f0ceda2ab81678fe6c8), before further concurrent tests and successful wake receipts.
- Original safe rollback deployment dpl_FmurJGjaAQTfrKAQnEFGFS76TKh3 remains available; disable ARA_WAKE_NOTIFY_ENABLED and redeploy or request rollback if issues.

## Scope boundary
This PASS covers fixed item 5, notifications from canonical Vercel controller to Hostinger broker. It does not prove Windows subscriber event-driven behavior (item 6), elimination of idle polling (item 7), fallback (item 10) or CU-hours (item 12). Do not activate another wake publisher or claim those later items complete.
