# Lease: Kwai Studio login fallback recovery
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_EXPIRES: 2026-10-06T11:15:00Z
BASELINE_PROVEN: native Kwai MAIN and real login chooser are reachable remotely; official studio.kwai.com currently exposes Phone Number and Verification Code fields.
FAILED_AVOIDED: do not repeat taps on the non-clickable native merged Phone text node; do not interpret Chrome first-run UI as Studio failure.
SUCCESS_SIGNAL: after dismissing Chrome first-run, official Studio page exposes editable Phone Number and Verification Code controls.
FAILURE_SIGNAL: Chrome first-run is cleared and 15 bounded navigation/reload variants still never expose the official login fields.
TEST_VALIDITY: Chrome package foreground, network available, and Studio URL actually loaded before classification.
