# Lease — Kwai Phone web continuation
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_OWNER: chatgpt-phone-web-continuation
LEASE_EXPIRES: 2026-10-06T15:13:00Z
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: run 37470899378 proves MAIN -> login chooser -> semantic Phone -> Chrome FirstRunActivity; subsequent current workflow contains deterministic Chrome FRE and notification-modal dismissal.
FAILED_AVOIDED: no direct non-exported Activities, no guessed deep links, no coordinate spray, no reopening MAIN/Phone discovery, and no separate studio.kwai.com navigation as a substitute for the Phone redirect.
SUCCESS_SIGNAL: continuing the exact browser surface opened by native Phone reaches a genuine editable auth form, provider handoff, or explicit OTP/challenge state, with package/activity/UI evidence.
FAILURE_SIGNAL: after FRE/notification dismissal the same Phone-originated browser surface deterministically reaches a non-auth dead end.
TEST_VALIDITY: emulator boot + apps installed + FSM_MAIN_REACHED + LOGIN_SURFACE_REACHED + semantic Phone action + Chrome foreground; no publication and no credential/OTP bypass.

## Objective
Instrument the legitimate Phone-originated browser continuation instead of abandoning it for an unrelated Studio navigation. Collect post-modal activity, UI, and URL/address-bar evidence and classify the first real auth boundary.
