# Final authority and failover policy — 2026-10-16

Verified production decisions:

- Anthares Remote principal: `anthares-remote-agent-v4-c8.exe`, Session 0, SYSTEM.
- Anthares Remote cold reserve: `anthares-remote-agent-v4.exe`.
- Failover grace in production: 5400 seconds (90 minutes).
- Real reserve takeover was proven with a real remote command; real return to `v4-c8` was also proven. Never run both executors concurrently.
- `Anthares Remote Recovery Watchdog` must remain enabled. It owns principal-health recovery. `Anthares Remote Failover Arbiter` owns reserve entry/exit.
- Windows-agent control remains `https://anthares-remote-primary.vercel.app`; private GitHub + GitLab queues remain recovery transports.
- Android runtime canonical authority is SYSTEM using ADB 5037.
- Interactive MEmu recovery + ADB 5038 is fallback only, after the SYSTEM path is exhausted. It must never become a parallel normal authority.
- Before entering the interactive fallback, MEmu is powered off. Health checks must not start ADB 5038 merely to probe it.
- When SYSTEM/5037 is healthy, ADB 5038 must be absent and the two fallback tasks must be disabled.
- Actual Windows reboot acceptance remains the last deferred test. Do not reboot merely to test this policy.
