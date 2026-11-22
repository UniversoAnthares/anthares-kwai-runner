# Lease: MEmu4 Kwai standby recovery
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-11-22
START: 2026-11-22T08:48:00-04:00
EXPIRES: 2026-11-22T09:18:00-04:00
OWNER: ChatGPT on user's direct operational repair request
BASELINE: MEmu_4 instance in Lucas Session 1 with ADB 5037, serial 127.0.0.1:21543; com.kwai.video installed, but screenshot at 08:46 entirely black while activity existed and focus=null. App-only force-stop and relaunch at 08:47 restored rendering and focus without changing login files. Physical Android remains on separate ADB 5038; daemon requires verified matching Kwai identity before failover.
RISK: no media upload or lease duplication; no uninstall, logout, state clear, VM reset, or copying auth credentials. Preserve physical primary.
PLAN: read-only authenticated profile verification; audit and minimally repair standby launcher only if needed; ensure app visible and preserve account session; test readiness with ADB.
SUCCESS: live identity and standby READY; active failover only after genuine physical failure and clean idempotency fencing.
CLOSURE: append finding with results and release lease.
