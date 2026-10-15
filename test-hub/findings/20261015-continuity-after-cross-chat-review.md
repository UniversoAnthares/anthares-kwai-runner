# Continuity after cross-chat review — 2026-10-15

STATUS: CURRENT
AREA: coordination
DATE: 2026-10-15

## Mandatory cross-chat sources
Before each new round, review the latest conclusions from the chat `Continuar resolução pendências` (and other active continuity chats when relevant), then run regression checks before advancing. Do not treat older quota/service states as current without fresh evidence. The cross-chat review is mandatory before each next fixed-list decision.

## Current hard constraints
- Anthares Remote is the only remote-control surface.
- Anthares Browser is the only browser-automation surface.
- WinRemote, MeshCentral, Browserless, TinyFish, Render and CircleCI are permanently retired. Never revive them because quota/status later improves; migrate any residual function when found.
- Codespaces is retired from TikTok/Kwai publication/session routes after factual review showed it is no longer part of the canonical Kwai publisher path.
- Do not confuse Browserless with Anthares Browser.
- GitHub Actions public hosted runners are currently usable; private-repository Actions are quota-blocked until reverified.
- GitLab CI is quota-blocked (`ci_quota_exceeded`) until reverified; GitLab Issues/API remains valid where already used by the ARA queue.
- Cloudflare Workers runtime is operational; Cloudflare Browser Rendering is a separate product and is not an active browser route.
- No reboot without explicit user authorization.

## Reconciliation with continuity work
The upload/publication chain has advanced beyond older notes: a controlled TikTok publication was completed and reconciled without duplication. Fixed-list items 9–11 subsequently consolidated Source → Clip → Publication and hardened the central publisher target semantics. Do not roll back to older statements that TikTok publication has never succeeded, or create a second queue/dedupe authority beside the Cloudflare control plane.

For the fixed F0-F22 infrastructure checklist, F15 remains a separate acceptance criterion: a real boot/logoff persistence test for the canonical ARA SYSTEM path. Process-kill recovery, Task Scheduler inspection and simulated restart are useful preflight evidence but are not equivalent to a real Windows boot.

## Current phase interpretation
- F14: closed; controlled C8/supervisor failures and queue failover have been exercised.
- F15: prepared but not closed. Boot and logoff verifier tasks are installed. Closing F15 requires an actual logoff/boot event. Reboot must not be issued without explicit user authorization.
- F16: closed as an audit-only phase.
- F17: re-check the latest Anthares Browser/Reserva state before action. Keep TikTok and Kwai identity/session evidence separate.

## Guidance for future agents
1. Re-read `Continuar resolução pendências` first, deeply enough to capture newer parallel work and decisions.
2. Re-read the latest `test-hub/findings` continuity/handoff notes and inspect current `main`; chats and repository can advance concurrently.
3. Re-run regression checks on already-passed phases before changing the next one.
4. Classify every failure before changing code: Anthares defect vs provider quota vs retired provider vs missing credential/manual authentication.
5. Never revive a retired provider as a shortcut.
6. Keep Cloudflare central control plane as the sole operational authority for enqueue/lease/fence/dedupe/reconcile unless an explicit migration replaces it atomically.
7. Mark evidence as VERIFIED, HISTORICAL or PENDING.
8. Do not claim F15 passed without a real boot/logoff proof.
