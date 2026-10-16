# Anthares Android Runtime — SYSTEM primary, interactive fallback

STATUS: PROVEN / IMPLEMENTED
DATE: 2026-10-16
AREA: android-runtime | memu4 | recovery-authority

## Final authority rule

The canonical authority is the SYSTEM Anthares Android Runtime.

Recovery order is fixed:
1. SYSTEM runtime attempts direct `MEmuManage startvm MEmu_4 --type headless`.
2. SYSTEM runtime uses isolated ADB server port 5038 and guest ADB repair.
3. Only after the direct SYSTEM path exhausts its bounded window may the interactive redundancy run.
4. Interactive redundancy uses `Anthares-MEmu4-Recovery-Launcher` plus `Anthares-MEmu4-ADB5038-Interactive`.
5. Redundancy tasks have no trigger and remain disabled outside an explicit fallback attempt.
6. A named global mutex `Global\AntharesMEmuRecoveryAuthority` prevents two runtime recovery attempts from acting simultaneously.
7. Fallback tasks are disabled again in `finally` after success or failure.

The interactive path is redundancy only. It is not a second authority, boot authority, watchdog or parallel controller.

## Practical validation

Installed runtime source commit: `f57d30cde9491311ebfb68aa6221df02de949c0a`.
Installed runtime SHA-256 observed after deployment: `7868E3C4AB2ACF820A1EDC1EEB246EDC5A1F7893775FD7E54EA3639C3F76EC0B`.

After deployment:
- `Anthares Android Runtime MEmu SYSTEM`: enabled, SYSTEM, AtStartup.
- `Anthares-MEmu4-Recovery-Launcher`: disabled, no trigger.
- `Anthares-MEmu4-ADB5038-Interactive`: disabled, no trigger.
- `Anthares-MEmu4-Interactive-Launcher`: disabled.
- MEmu runtime health: `running`, transport=`device`, boot_completed=true, `com.kwai.video` installed, healthy=true.

Mutex proof:
- a detached test process acquired `Global\AntharesMEmuRecoveryAuthority`;
- a concurrent runtime `recover -Target memu -AllowBackendStart` returned `action=recovery_busy` and `reason=another_anthares_runtime_recovery_holds_authority`;
- no fallback task was required.

No Windows reboot, shutdown or logoff was performed.
