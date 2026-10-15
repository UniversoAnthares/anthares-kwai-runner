# F17-F22 reconciled status — 2026-10-15

STATUS: CURRENT
AREA: publication / reserve persistence / final integration
DATE: 2026-10-15

## Mandatory continuity rule
Before changing any of these statuses, re-read the latest state of the chats `Continuar resolução pendências` and `SISTEMA DE UPLOADS`, then inspect current `main` and fresh live health. Do not revive an older route merely because it has stronger repository artifacts.

## Architecture correction
The old interpretation of F21 (remove Android/emulator production dependency after browser-only publishing) is superseded.

Current intended social execution architecture:
- Android/mobile physical device is the preferred Kwai execution path.
- MEmu4 remains a deliberate redundancy for Android social execution, not something to remove.
- TikTok currently has a separately proven publication path; do not assume it uses the same executor as Kwai without fresh evidence.
- Public GitHub-hosted Android/KVM remains a tested/implemented alternate route, but its latest v17 publisher run is not evidence that the physical-device route failed.
- PC-local MEmu is redundancy, not the normal primary path.

The only MEmu4 acceptance still deferred is a real-boot proof that it starts automatically, headless/invisible and muted. That proof is grouped with F15 at the end.

## F17-F19 — correction
These phases refer to the working Kwai operational path, not necessarily the GitHub-hosted Android/KVM experiment.

- F17 — authenticated Kwai session: CLOSED on the current operational Android/mobile path based on current cross-chat operational confirmation. Do not reopen merely because an alternate v17 cloud publisher run failed.
- F18 — publication surface: CLOSED on the current operational Android/mobile path.
- F19 — real Kwai publication: CLOSED on the current operational Android/mobile path; the user confirms Kwai posting is already functioning. Treat this as operationally confirmed evidence, distinct from the failed/unfinished alternate GitHub-hosted Android/KVM route.

Evidence classification for F17-F19: OPERATIONALLY CONFIRMED by current project state/user confirmation; alternate cloud-route proof remains separate and must not override it.

## F20 — Anthares Reserva persistence
CLOSED for persistence capability.

Fresh live health returned HTTP 200 with:
- `browser_binding=true`
- `durable_state_binding=true`
- `persistent_profile_support=true`
- `render_required=false`

Current source persists encrypted browser state in the `BrowserState` Durable Object, using SQLite-backed Durable Object storage, and implements capture/restore of cookies + localStorage plus persisted browser session id. The state payload is AES-GCM encrypted before durable storage. `wrangler.toml` binds `BROWSER_STATE` to `BrowserState` and declares the SQLite migration.

Important boundary: F20 proves persistence machinery/capability. Account authentication validity is not the F20 acceptance criterion; that belonged to F17 and must not be conflated with the public `/health` field `authenticated_session=not_verified`.

## F21 — Android primary + MEmu4 redundancy
CLOSED as architecture/role definition, superseding the old 'remove emulators' wording.

Accepted state:
- Android/mobile physical route is primary for Kwai.
- MEmu4 is retained as redundancy.
- MEmu4 boot behavior is NOT part of this closure; real boot validation (autostart + hidden/headless + muted) is explicitly deferred to the final boot round with F15.
- Do not delete or decommission MEmu4 under the old F21 text.

Current Windows preflight already has a SYSTEM boot task for MEmu4 and the VM audio configuration was changed to disabled; however only a real reboot can prove the complete boot behavior, so that one proof remains deferred.

## F22 — integrated validation/documentation
CLOSED for the current non-reboot integrated stack.

Fresh live checks on 2026-10-15:
- `anthares-control /health` => 200, version `publisher-target-v17`, `persistent_state=true`, `queue_bound=true`, `pc_fallback=false`.
- `anthares-ara-backup /healthz` and `/_selftest` => 200; persistence cycle true; create/idempotency/lease/result all true.
- `anthares-ara-reserva /healthz` and `/_selftest` => 200; same persistence and self-test checks true.
- `anthares-reserva-browser /health` => 200 with browser and durable-state bindings true.
- Anthares Remote heartbeat was connected with no queued/leased/uncertain jobs at the time of the audit.

Deferred final boot-only acceptance is intentionally outside this F22 closure:
1. F15 real Windows boot/logoff persistence proof for Anthares Remote.
2. MEmu4 real Windows boot proof: automatic startup, invisible/headless, muted.

## Critical correction for next agents
The old `Anthares Remote Recovery Watchdog` must remain disabled per user decision. Do not re-enable it as part of F15. The canonical SYSTEM supervisor must be independently boot-startable/restartable. A live audit found the running SYSTEM supervisor/C8 process healthy, but the canonical scheduled startup task was not visible in the current task listing after watchdog disablement; an attempted direct re-registration from the interactive Anthares Remote shell was denied by Windows elevation. An ARA private-queue repair issue was opened as `UniversoAnthares/anthares-ara-queue#133`; verify/reconcile it before the final reboot. Do not reboot until the canonical SYSTEM startup task is positively present and enabled.

## Final status
- F17 CLOSED — operational Kwai authenticated path.
- F18 CLOSED — operational Kwai publishing surface.
- F19 CLOSED — real Kwai publication already operationally confirmed.
- F20 CLOSED — Reserva durable persistence machinery proven.
- F21 CLOSED — Android/mobile primary + MEmu4 redundancy architecture; boot proof deferred.
- F22 CLOSED — integrated non-reboot validation and documentation.
- F15 remains deferred to the final boot round, together with MEmu4 boot behavior validation.
