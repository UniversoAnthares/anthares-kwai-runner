

## 2026-10-12 — Agent 3 — historical native-create/auth archaeology consolidated
- Canonical SHARED-LOG was re-read before this consolidated write.
- Old-chat archaeology, starting from `Branch - Atualizar testes de publicação` and `Continuar pesquisa Kwai API`, confirms the previously successful local setup used an already-authenticated MEmu instance (historically MEmu2 during the first successful period). The chats do not preserve how that original native login was performed; no phone/password/QR/provider method can be asserted from the historical record.
- Historical native creation control was `com.kwai.video.basis:id/id_record_layout`, used via a 1200 ms long press on the bottom-center create control to open Album. Commit `de1eaf8d` later added `com.kwai.video.basis:id/fake_add_button` as a real bottom-bar variant. Commit `a64df3d` added semantic create/camera/+ matching plus a bottom-center 90%-height 1200 ms long-press fallback.
- Commit `a7de273b` proves the reliable Home recovery: resolve the Kwai launcher then use `am start -S --activity-clear-task`, because force-stop + monkey could restore ShareActivity without the bottom bar. It actively waited until the native create control appeared; this path was verified historically with `KWAI_MEMU_PREPARE=OK_NOT_PUBLISHED`.
- The isolated v0.2.2 publisher already contains these native create/cold-start mechanisms. Its current probe failure therefore reflects the fresh VM3 still being on Tiny/PWA/guest state rather than missing button-discovery logic.
- Searched current PC for recoverable old MEmu2/session artifacts; no historical MEmu2 disk/image, `kwai-session.enc`, or `kwai_storage_state.json` was found in the inspected runtime roots. Current MEmu configuration belongs to the fresh reinstall.
- Recovered the modern native session mechanism: encrypted full `/data/user/0/com.kwai.video` state (`kwai-session.enc`) saved/restored and identity-checked as `lucasrosalem`, backed by the private Cloudflare session vault. This is suitable to bootstrap the reconstructed VM3 if a valid vault session exists.
- Triggered the allowlisted `Anthares Kwai Queue Publisher` mobile-auth recovery through `.kwai-queue-trigger`, commit `12c477c34331d10054a62ec72dae83fb60b7806a`. Run `38306277632` is active; all 30 phone-auth contract cases passed and `mobile_auth_bootstrap` is currently testing the prior encrypted session in Android before deciding whether an interactive phone-auth window is required.
- TinyFish profile inventory also found an existing profile with a recorded GitHub sign-in (`GitLab Runner Admin`), giving a browser fallback for explicitly dispatching the independent `Kwai Mobile Auth Acceptance` workflow if the queue bootstrap cannot recover the prior session.
- No Kwai publication occurred in this investigation.
- Next: poll run 38306277632. If its prior encrypted session authenticates as `lucasrosalem`, reuse that native state for VM3; otherwise run the independent credential-based mobile-auth acceptance workflow and seal a fresh session, then restore it into VM3 before the native create/probe/prepare milestones.

## 2026-10-12 — Agent 3 — Anthares Local Executor v1 daemon created
- Canonical SHARED-LOG was re-read immediately before this step.
- Added `anthares_local_executor.py` on isolated branch `UniversoAnthares/anthares-clipper:legacy-pc-rebuild`, commit `4c0db8ec0af779725e39c6a348be79a005d8a520`.
- Executor is allowlist-only; there is no arbitrary shell action.
- Current fixed actions: `status`, `tiktok_session`, `tiktok_prepare`, `tiktok_qa`, `tiktok_publish`, `kwai_probe`, `kwai_prepare`, `kwai_publish_local`.
- Publish actions require two independent gates: queue request must set `publish=true` and a local runtime guard file must exist (`ALLOW_TIKTOK_PUBLISH` / `ALLOW_KWAI_PUBLISH`).
- Queue protocol is immutable JSON request files under `executor-control/inbox/`; result files are written under `executor-control/results/` and committed back to the isolated Git branch.
- Executor refuses unknown actions, arbitrary args, malformed/non-UUID request IDs, and local code dirtiness before syncing.
- Heartbeat/lock state lives outside git under `D:\AntharesWork\legacy-pc-runtime\executor`.
- This work is isolated from the other agent's active Kwai VM3/auth path; no Kwai/TikTok publication occurred.
- Next: create queue schema/helper, watchdog and installation scripts; then stage files on PC and test only `status`/safe non-publish actions.
