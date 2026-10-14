# Render retirement policy — 2026-10

Render is retired as an Anthares execution platform. It must not be used as primary, secondary, emergency fallback, QA runner, browser worker, publication worker, MCP gateway, control plane, persistence layer, keepalive target, scheduled probe, or job executor.

## Canonical replacements

- ARA private execution: GitHub + GitLab private issue queues under SYSTEM/session 0.
- ARA control/state: Cloudflare Workers + Durable Objects/SQLite where HTTP control is explicitly needed.
- ARA MCP/OAuth: Cloudflare Worker `anthares-ara-mcp`.
- Independent PostgreSQL/fencing: Neon-backed PostgreSQL authority.
- Container/browser compute: Northflank where persistent container compute is required and capacity exists.
- Finite CI/execution: GitHub Actions and GitLab SaaS/shared runners.

## Invariants

1. Operational source code must not contain an `onrender.com` default or fallback.
2. No scheduled workflow may wake, probe or keep a Render service alive.
3. No Render-hosted runner may retain a GitLab runner token.
4. No Render-hosted publication/control/MCP worker may retain execution credentials.
5. Persistent state must live outside Render.
6. A service is migrated only after its replacement is proven and its Render execution path is disabled.
7. Remaining Render resources may exist temporarily only as inert account objects pending physical suspension/deletion; their existence is not permission to execute work.

## Current migration evidence

- TikTok container path is served through the Cloudflare router with Northflank as the configured upstream and no Render fallback.
- Central social routing revision `2026-10-14-render-retired-r2` excludes Render from priorities and probes.
- ARA private GitHub and GitLab queues have both consumed real jobs from `DESKTOP-FTDK0HP`; the SYSTEM supervisor reports `github_queue=true`, `gitlab_queue=true`, and `http_control_enabled=false`.
- Render-hosted GitLab runner credentials were cleared so those services cannot pull jobs after redeploy.
- Render-hosted MCP/control/X/TikTok execution credentials were cleared or invalidated so they cannot accept authenticated task execution after redeploy.
- Scheduled Render browser/GitLab keepalive jobs were retired.
- Neon/PostgreSQL self-test and fencing checks are healthy and independent of Render.

## Physical-resource cleanup

Render account objects must be suspended or deleted once the management surface exposes that operation. Until then they remain credential-disabled and absent from all routing and scheduling.
