# Cloudflare write-amplification correction plan

STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-15

## Confirmed hot paths
- `cloudflare-ara-backup`: every `/v1/device/heartbeat` performs an UPSERT into Durable Object SQLite, even if payload is effectively unchanged.
- `cloudflare-ara-mcp`: one-time OAuth consumption records are written to Durable Object storage and require bounded retention/cleanup.

## Required correction
- coalesce heartbeat writes: do not persist every poll; persist only when semantic payload changes or a minimum persistence interval expires.
- keep connection freshness in memory where possible while retaining a bounded durable checkpoint interval.
- expire/delete consumed OAuth markers after their token expiry window, without weakening replay protection.
- preserve fail-closed lease, dedupe, fencing and UNCERTAIN semantics.
- Cloudflare returns only as a redundant provider after fresh quota and behavior proof.
