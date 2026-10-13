# PROVEN — ARA shared fencing via independent Floot/PostgreSQL authority

Date: 2026-10-13

## Architecture
- Independent fencing authority: `https://anthares-ara-reserva.floot.app/_api/ara/fence`.
- Durable authority state: Floot-managed PostgreSQL (Neon), separate from Cloudflare Durable Objects and Render.
- Primary/active ARA controller: `https://anthares-ara-backup.anthares1.workers.dev`.
- Device: `DESKTOP-FTDK0HP`.
- The authority stores only the enrolled SHA-256 of the device bearer token, never the bearer plaintext.
- Per-device lease fields: owner, epoch, lease deadline, update time and controller nonce.
- Acquire is serialized with a PostgreSQL row lock. A live lease held by another owner returns conflict; a stale nonce cannot renew or release a newer lease.
- Controller fencing TTL is 180 seconds, longer than the ARA maximum single remote command timeout (120 seconds).

## Cloudflare integration
`cloudflare-ara-backup/src/index.js` now fails closed before heartbeat acceptance or new job leasing unless the independent authority authenticates the device and confirms/acquires the Cloudflare controller lease.

Production `/healthz` returned:
- `ok=true`
- `independent_of_render_postgres=true`
- `shared_fencing="floot-postgres-v1"`

## End-to-end authentication proof
The real Windows agent authenticated to Cloudflare with its existing device bearer. Cloudflare forwarded that bearer only to the user-owned fencing authority. The authority validated its SHA-256 against the enrolled device hash and created/renewed the real production fence row.

Observed production fence after deployment:
- device: `DESKTOP-FTDK0HP`
- owner: `https://anthares-ara-backup.anthares1.workers.dev`
- epoch: `1`
- TTL: `180` seconds
- renewal timestamp advanced after deployment, proving continued authenticated renewals from the live device path.

Negative authentication checks:
- invalid bearer against Floot fencing endpoint => HTTP 401 `unauthorized`
- missing bearer against Cloudflare `/v1/device/auth-check` => HTTP 401 `unauthorized`

The Cloudflare MCP gateway root simultaneously reported `control_ready=true` and `device_connected=true`.

## Safety invariant
A controller cannot lease a new ARA job without owning the independent PostgreSQL fence. The reserve remains execution-disabled until it can acquire the same per-device fence, so Cloudflare and the reserve cannot both be authorized to begin new work for the same device at the same time.

No device token, private key, access token or Cloudflare credential is recorded in this finding.
