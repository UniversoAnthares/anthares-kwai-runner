# F15 / MEmu4 final pre-boot reconciliation — 2026-10-16

STATUS: CURRENT

Fresh live audit after the user's three Windows reboots and subsequent cleanup:

- `Anthares Remote Agent SYSTEM` is enabled, BootTrigger, SYSTEM, and currently running.
- Current canonical agent is exactly `anthares-remote-agent-v4-c8.exe` in Session 0 under the SYSTEM supervisor.
- `Anthares Remote Agent User` is disabled.
- `Anthares Remote Recovery Watchdog` is disabled and must remain disabled.
- `Anthares Remote Recovery` remains enabled as an independent periodic supervisor-presence repair task; it is not the retired watchdog loop.
- `Anthares Remote Recovery Test Once` was disabled as test residue.
- Current control plane is Vercel+Neon (`https://anthares-remote-primary.vercel.app`) with GitLab + GitHub private issue queues for recovery. Do not revert this to the older Cloudflare-primary description.

## MEmu4 correction

The earlier assumption that any `MEmu.exe` process necessarily meant a visible GUI was too strict. Fresh runtime proof showed the working MEmu9 bootstrap `MEmu.exe MEmu_4 -b` has `MainWindowHandle=0` and no title, while it starts the same `MEmu_4` backend and makes Android operational. It is therefore a background bootstrap, not a second VM or a visible emulator window.

Current working runtime proof:
- one `MEmu_4` Android instance;
- `MEmuHeadless.exe --comment MEmu_4` present;
- background `MEmu.exe MEmu_4 -b` has no visible main window;
- VM audio configuration is `audio=none`, `audio_out=off`, `audio_in=off`;
- ADB `127.0.0.1:21543` on daemon port 5038 returns `device`;
- `sys.boot_completed=1`;
- `pm path com.kwai.video` returns the installed Kwai package.

Residual interactive/test launchers were disabled, including the plain `MEmu.exe MEmu_4` launcher, `memuc start` launcher, duplicate boot/recover tasks, ADB interactive task, Native Execmd probe, NativeStart/probe/screenshot/session test tasks and other one-shot test helpers.

Canonical boot strategy was hardened:
- `Anthares MEmu4 Headless Boot` is enabled again as SYSTEM + BootTrigger and points to `memu4-boot-headless.ps1` v10.
- v10 first attempts true hypervisor headless start; if MEmu9 cannot bring Android online that way, it automatically falls back to `MEmu.exe MEmu_4 -b`, which is background/no-window, then requires ADB `device` before success.
- `Anthares-MEmu4-Recovery-Launcher` is an AtLogon Lucas fallback with the same background `-b` semantics, deduped by checking ADB first.

## Remaining acceptance

F15 Windows boot persistence is strongly evidenced by the user's three real reboots plus live SYSTEM/Session-0 state. The only final proof that still must be collected after the configuration above is a fresh user-initiated Windows reboot confirming the *new* MEmu boot strategy: automatic start, no visible MEmu window, audio disabled, ADB device, Android boot complete, Kwai installed, and one canonical ARA C8 in Session 0.

Do not reboot, shut down, or log off Windows automatically. The user explicitly requires that any reboot/logoff be performed only by the user after being asked.
