# F17 — Kwai session persistence — PROVEN

STATUS: PROVEN / CLOSED
DATE: 2026-10-16
AREA: Kwai | MEmu_4 | Anthares Android Runtime

## Acceptance target

Prove the exact Kwai owner session for `@lucasrosalem` persists across Android backend restart/recovery, without publishing content.

## Fresh evidence from this round

The canonical Anthares Android Runtime recovered/restarted the `MEmu_4` Android backend without rebooting, shutting down or logging off Windows.

After backend recovery/power-cycle, Kwai was opened and the Profile surface was read semantically. The visible UI contained all of the following owner-session signals:
- exact normalized handle: `lucasrosalem` (Kwai renders the handle without `@` in this app version);
- owner-only control: `Editar perfil`;
- display name: `Lucas Rosalem`;
- profile navigation labels including `Seguidores`, `Seguindo`, `Publicações` and `Perfil`;
- foreground package: `com.kwai.video`.

The canonical identity contract normalizes either visible `lucasrosalem` or `@lucasrosalem` to the expected identity `@lucasrosalem`, but only when the Kwai package is foreground and an owner-only profile control such as `Editar perfil`/`Edit profile` is also present.

No publication command was issued for this proof. No content was posted. No account data was cleared or reinstalled.

## Continuity conclusion

F17 is CLOSED. The authenticated exact owner session survived backend restart/recovery. A Windows reboot is not required for F17 and belongs only to the deferred F15 boot acceptance.

F18-F20 remain closed from their prior proofs and do not need to be rerun because of this reconciliation.
