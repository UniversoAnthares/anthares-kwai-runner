# F16 — Anthares Reserva audit without publishing

STATUS: PROVEN
AREA: session
DATE: 2026-10-15
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

## Scope
Original fixed phase F16: audit Anthares-Reserva without publishing.

## Fresh runtime audit
The current endpoint `https://anthares-reserva-browser.anthares1.workers.dev` was inspected directly without invoking any publication route.

`GET /health` returned HTTP 200 with:

- service=`anthares-reserva-browser`;
- version=`2026-10-13-reserva-browser-v4`;
- provider=`cloudflare`;
- mode=`on-demand`;
- browser_binding=true;
- durable_state_binding=true;
- live_view=true;
- persistent_profile_support=true;
- authenticated_session=`not_verified`;
- render_required=false;
- backend purpose=`emergency browser continuity`;
- generic browser support enabled;
- TikTok recovery support enabled.

`GET /owner` returned the protected owner login surface (`Anthares Reserva Browser`) and does not expose an authenticated owner session without the owner code.

Protected machine routes reject unauthenticated access:

- `POST /tiktok/session/verify` => HTTP 401 without the reserve token;
- `GET /tiktok/northflank/status` => HTTP 401 without the reserve token.

The deployed composition uses a Cloudflare owner/control surface and bridges interactive Chromium to the Anthares Browser/Northflank runtime. Current source encrypts persisted browser state with AES-GCM derived from `ANTHARES_RESERVA_TOKEN`, uses a Durable Object state binding, and does not require Render.

## Important audit findings

1. F16 is an audit phase, not an authentication proof. Current health explicitly reports `authenticated_session=not_verified`; this remains the entry condition for F17.
2. The health payload advertises `authenticated_probe_path=/session/verify`, but the currently deployed protected verification route is `POST /tiktok/session/verify`. The old `/session/verify` probe returned 404. This documentation/health mismatch should be corrected before relying on automated session checks.
3. The current owner bridge is explicitly centered on TikTok recovery in `northflank-owner-entry.js`; no Kwai publication was attempted or inferred from this audit.
4. TinyFish and Browserless are excluded from the operational path and were not used. Browserless and TinyFish are treated as unavailable while their quotas are exhausted.
5. No Render or CircleCI path was used.

## Result
F16: PASSED as an audit-without-publication phase.

F17 remains OPEN and must prove a real persisted authenticated target session before any publishing phase advances.