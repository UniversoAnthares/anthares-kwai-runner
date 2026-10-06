# Lease — semantic Kwai Phone parent/action discovery
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_EXPIRES: 2026-10-06T14:00:00Z
BASELINE_PROVEN: Android runtime reaches MAIN and Welcome to Kwai chooser; Phone label exists but center-coordinate tap leaves blank UI / no editable field.
FAILED_AVOIDED: no deep links, no direct non-exported Activity, no coordinate spray, no Studio browser.
SUCCESS_SIGNAL: legitimate chooser Phone transition reaches editable phone field or explicit phone/OTP challenge using accessibility semantics/ancestor click/action evidence.
FAILURE_SIGNAL: semantic ACTION_CLICK on clickable Phone node/ancestor plus keyevent/scroll fallback cannot transition despite valid chooser state.
TEST_VALIDITY: dump full Phone node ancestry, clickable/focusable/enabled attributes, bounds and post-action package/activity/UI.
