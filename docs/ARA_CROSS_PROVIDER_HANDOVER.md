# Cross-provider ARA reconciliation gate

The Cloudflare Durable Object has the authoritative queue for jobs previously submitted to that controller. The Floot/Neon authority is authoritative for per-device owner/epoch/nonce fencing. Neither database alone can prove an entire cross-provider handover is safe.

New signed, read-only endpoint (staged, not deployed):
GET /v1/mcp/reconciliation?device_id=DESKTOP-FTDK0HP
Requires the existing Ed25519 MCP service signature with replay protection.
Returns queued, leased and uncertain counts, non-secret job metadata, and safe_to_promote.
No job args or command outputs are exposed.

Important: safe_to_promote is only a point-in-time diagnostic, not a promotion authorization. To enable promotion, implement a Cloudflare handover barrier in the Durable Object which atomically rejects new job creation/dispatch for that device, takes a stable queue snapshot, and transfers only safe queued jobs to Floot with identical IDs/idempotency keys. Unknown leased/uncertain jobs require reconciliation; do not replay them. Bind a handover generation to the shared PostgreSQL fencing epoch and have the Windows agent validate it before side effects. Disable automatic promotion until end-to-end tests demonstrate no split-brain.

Do not deploy the staged reconciliation endpoint until tests and deployment controls are reviewed. Preserve the active Worker.
