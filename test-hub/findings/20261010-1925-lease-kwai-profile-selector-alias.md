# Lease: repair verified Kwai main-navigation Profile alias
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-10
OWNER: chatgpt-kwai-gitlab-followup-1925Z
LEASE_UNTIL: 2026-10-10T19:45:00Z
BASELINE_PROVEN: Android run 38079218107 passed 33 tests, installed Kwai, produced 22 valid UI dumps with main_navigation=true and focus=kwai, but profile_taps=0 and no chooser; prior authentic UI evidence includes ll_profile. Publisher run 38079188085 reached actual native Email EditText but was blocked before identity verification.
FAILED_AVOIDED: no blind 110s loop, no 40-way QA, no secret-backed login while credential exposed; no public screenshots or artifacts.
SUCCESS_SIGNAL: semantic Profile selector recognizes both id_home_bottom_tab_me and ll_profile; unit tests pass; one credential-free bounded Android run records PROFILE_TAP_COUNT>=1 and ideally native chooser/form visible.
FAILURE_SIGNAL: no Profile alias in valid UI, profile tap fails to navigate, or selector test regression.
TEST_VALIDITY: verify actual Kwai foreground, valid XML, no credential input; green synthetic tests do not prove login or publication.
SECURITY: Public screenshot credential exposure in run 38079188085; 18 public artifacts purged in run 38079625643. Password rotation required; scheduled publisher paused.
