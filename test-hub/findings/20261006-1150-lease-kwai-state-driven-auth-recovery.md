# Lease: Kwai state-driven auth recovery
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_EXPIRES: 2026-10-06T12:15:00Z
BASELINE_PROVEN: run 37455005102 had credentials present and Kwai launched, but autologin never reached login because Pixel Launcher ANR dominated; run 37454956004 proves kwai_state_driver.py recovers launcher state and reaches FSM_MAIN_REACHED + LOGIN_SURFACE_REACHED.
FAILED_AVOIDED: do not launch 30 simultaneous real credential attempts; parallelism is limited to non-credential launcher/FSM recovery. Exactly one credential attempt follows a proven normalized MAIN state.
SUCCESS_SIGNAL: state-driven runtime reaches MAIN, then one bounded credential attempt emits authenticated correct-account READY proof or explicit OTP/challenge state.
FAILURE_SIGNAL: state-driven MAIN is proven but one bounded credential attempt cannot reach an editable auth method.
TEST_VALIDITY: credential failure is not classified unless FSM_MAIN_REACHED and LOGIN_SURFACE_REACHED occurred first.
