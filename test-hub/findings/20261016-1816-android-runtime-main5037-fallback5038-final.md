# FINAL RECONCILIATION — Android Runtime ADB authority

- Verified live without reboot on 2026-10-16.
- Primary authority: SYSTEM/headless Android Runtime.
- Primary ADB server: 5037.
- Interactive ADB 5038 is fallback-only, disabled by default, and has no listener during healthy primary operation.
- Live proof after handoff: 127.0.0.1:21543 = device on 5037; sys.boot_completed=1; com.kwai.video installed; runtime memu.healthy=true.
- Fallback tasks Anthares-MEmu4-Recovery-Launcher and Anthares-MEmu4-ADB5038-Interactive remain disabled by default and are activated only after primary exhaustion under the recovery mutex.
- MEmu audio is none/off; MEmu and MEmuHeadless have MainWindowHandle=0.
- Final real reboot acceptance remains intentionally pending owner action.
