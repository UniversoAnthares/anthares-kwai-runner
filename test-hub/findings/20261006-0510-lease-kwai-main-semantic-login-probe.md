# Lease: Kwai MAIN semantic login probe
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_EXPIRES: 2026-10-06T06:15:00Z
BASELINE_PROVEN: run 37416199342 reached APPS_INSTALLED and FSM_MAIN_REACHED. MAIN UI exposed a Log in control with Home, Discover, Inbox and Profile.
FAILED_AVOIDED: do not depend on AccessibilityService binding because the same run showed the service was not enabled. Do not reuse discarded URI or non-exported Activity routes.
SUCCESS_SIGNAL: semantic UIAutomator tap on visible MAIN Log in reaches an authentication surface with an editable field or explicit phone, email, or continue controls.
FAILURE_SIGNAL: after FSM_MAIN_REACHED and LOGIN_CONTROL_VISIBLE, semantic tap produces no authentication surface.
TEST_VALIDITY: APPS_INSTALLED, FSM_MAIN_REACHED and LOGIN_CONTROL_VISIBLE must occur before evaluating the hypothesis.
