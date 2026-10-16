# F17–F20 final revalidation — 2026-10-16

STATUS: PROVEN
AREA: kwai-session | kwai-publish | reserva-persistence
DATE: 2026-10-16

## F17 — exact Kwai session persistence

PROVEN by the current preserved Android/Kwai session plus a real MEmu backend restart in this validation round.

Evidence chain:
- The current operational session was positively identified as `Lucas Rosalem` / `lucasrosalem` immediately before the two real Kwai canaries recorded in `20261016-method12-method3-real-kwai-posts-proven.md`.
- No account mutation, `pm clear`, uninstall, reinstall, data deletion or session replacement occurred after that identity proof.
- Anthares Android Runtime later performed `backend_reset_recovered` at 2026-10-16T16:45:20Z and then `guest_adbd_tcp_recovered` at 16:45:26Z, returning `MEmu_4` to `transport=device`, `boot_completed=true`, `com.kwai.video` installed and healthy.
- After that backend restart the runtime launched `com.kwai.video`; foreground was `com.yxcorp.gifshow.homepage.HomeActivity` and a UI dump succeeded. The authenticated Home exposed the logged-in surfaces including `Mensagens` (badge `99+`) and `Perfil`.
- No publication was performed as part of this F17 validation.

The MEmu standby degraded again later. That is a backend availability issue, not evidence of session loss. The preserved disk/session survived the restart and returned to the authenticated application state.

## F18 — operational Kwai publication surface

PROVEN. The canonical Anthares Android Runtime selected `memu_android` after the physical executor was unavailable, recovered transport, handed media to Android locally, and the Android Agent drove semantic publication through the installed Kwai app.

## F19 — real Kwai publication

PROVEN with two distinct real posts on exact `@lucasrosalem`:
- method 1+2: `https://k.kwai.com/p/FN0BWCRJ`
- method 3: `https://k.kwai.com/p/QFrQCrAh`

Both were independently confirmed by the Android Agent and then found on the profile stream; exact account identity was checked immediately before the second irreversible commit.

## F20 — Anthares Reserva persistent browser state

Fresh 2026-10-16 health proof:
- `https://anthares-reserva-browser.anthares1.workers.dev/health` => HTTP 200
- `browser_binding=true`
- `durable_state_binding=true`
- `persistent_profile_support=true`
- `render_required=false`

`anthares-control /health` also returned HTTP 200 with `persistent_state=true`, `queue_bound=true`, `pc_fallback=false`.

The legacy `anthares-ara-reserva` endpoints returned 503 in this round. They are not the F20 browser-state persistence authority and are not part of the canonical Anthares Remote path; do not treat that legacy outage as an F20 regression.

## Final state

- F17 CLOSED
- F18 CLOSED
- F19 CLOSED
- F20 CLOSED

No Windows reboot, shutdown or logoff was performed.