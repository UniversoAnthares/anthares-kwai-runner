# Render retirement policy — 2026-10

Render is no longer an allowed canonical dependency. It may remain only as a final emergency fallback until its free resources expire.

## Canonical replacements

- ARA control/state: Cloudflare Workers + Durable Objects/SQLite.
- ARA MCP/OAuth: Cloudflare Worker `anthares-ara-mcp`.
- ARA independent recovery: private GitHub/GitLab issue queues.
- PostgreSQL/HA experiments: Neon project `anthares-ara-ha`.
- Container/browser compute: Northflank.
- CI, validators and probes: GitHub Actions and GitLab CI.

## Render services by disposition

### Already superseded; fallback only
- `anthares-ara-control`
- `anthares-remote-mcp`
- `anthares-remote-mcp-v2`
- `anthares-ara-infra-canary`
- `anthares-ara-infra-canary-v2`
- PostgreSQL `anthares-ara-state`

### Migration in progress to Northflank
- `anthares-x-render-worker-v3`
- `anthares-remote-control` browser/runtime surface

### CI/test/probe workloads; move to GitHub/GitLab and do not treat as services
- `anthares-browser-qa-render`
- `anthares-browser-qa-render-v2`
- `anthares-x-render-worker-authprobe`
- `anthares-x-upload-bench`
- `anthares-x-microcut-e2e`
- `anthares-x-real-fullflow-test`
- `anthares-gitlab-qa-runner`
- `anthares-gitlab-kwai-qa-isolated`
- `anthares-gitlab-kwai-qa-bootstrap`
- `kwai-up-validator`
- `kwai-up-uiauto-builder`
- `anthares-legacy-executor-probe`
- `anthares-youtube-source-probe`

### Social/browser workers requiring separate runtime verification before retirement
- `anthares-tiktok-render`
- `anthares-tiktok-render-v2`
- `anthares-tiktok-render-rootless`

## Invariants

1. No new code may use an `onrender.com` endpoint as its first or only route.
2. Any Render endpoint must be last in a failover list or guarded by an explicit emergency flag.
3. Persistent state must live outside Render.
4. A migration is complete only after a real operation succeeds on the replacement service.
5. Do not delete the Render fallback until the replacement has passed its real-operation check.
