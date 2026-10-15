# Continuity after cross-chat review — 2026-10-15

STATUS: CURRENT
AREA: coordination
DATE: 2026-10-15

## Mandatory cross-chat sources
Before each new round, review the latest conclusions from the chats `Continuar resolução pendências` and `SISTEMA DE UPLOADS`, then run regression checks before advancing. Do not treat older quota/service states as current without fresh evidence.

## Current hard constraints
- Anthares Remote is the only remote-control surface.
- Anthares Browser is the only browser-automation surface.
- Do not use WinRemote, MeshCentral, Browserless, TinyFish, Render, CircleCI or Codespaces for TikTok/Kwai.
- Browserless and TinyFish are currently excluded because quota is exhausted; do not confuse Browserless with Anthares Browser.
- GitHub Actions public hosted runners are currently usable; private-repository Actions are quota-blocked until reverified.
- GitLab CI is quota-blocked (`ci_quota_exceeded`) until reverified; GitLab Issues/API remains valid for the ARA queue.
- Cloudflare Workers runtime is operational; Cloudflare Browser Rendering is quota-blocked historically and must not be assumed available.
- No reboot without explicit user authorization.

## Reconciliation with the two continuity chats
The most recent continuity work shows that the upload/publication chain has advanced beyond several older notes: a controlled TikTok publication was completed and reconciled without duplication, and the next upload-system work is the Source → Clip → Publication consolidation. Do not roll back to older statements that TikTok publication has never succeeded.

For the fixed F0-F22 infrastructure checklist, however, F15 still has a distinct acceptance criterion: a real boot/logoff persistence test for the canonical ARA SYSTEM path. Process-kill recovery, Task Scheduler inspection and simulated restart are useful preflight evidence but are not equivalent to a real Windows boot because they cannot prove startup ordering, SYSTEM task launch after kernel/session initialization, network availability after boot, or absence of hidden dependence on the interactive session.

## Current phase interpretation
- F14: closed; controlled C8/supervisor failures and queue failover have been exercised, with fresh regression checks showing one SYSTEM/Session 0 C8 and no competing interactive executor.
- F15: prepared but not closed. Boot and logoff verifier tasks are installed. Closing F15 requires an actual logoff/boot event. Reboot must not be issued without explicit user authorization.
- F16: closed as an audit-only phase. Anthares Reserva is healthy, protected and persistent-state capable; authenticated session verification belongs to F17.
- F17: do not assume the old `not_verified` state is final. Re-check the latest Anthares Browser/Reserva state before action, especially because the continuity chat records later TikTok publication success elsewhere in the pipeline. Keep TikTok and Kwai identity/session evidence separate.

## Guidance for future agents
1. Re-read the two continuity chats first.
2. Re-run regression checks on already-passed phases.
3. Classify every failure before changing code: system defect vs provider quota vs retired provider vs missing credential/manual authentication.
4. Never revive a retired provider as a shortcut.
5. Mark evidence as VERIFIED, HISTORICAL or PENDING.
6. Do not claim F15 passed without a real boot/logoff proof.
