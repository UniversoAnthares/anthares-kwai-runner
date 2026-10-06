# Kwai Phone auth probe — two harness causes isolated
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-06
RUNS: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37417529886 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37417842391
BASELINE_PROVEN: FSM_MAIN_REACHED and LOGIN_SURFACE_REACHED.
FAILED_AVOIDED: do not classify these runs as Phone-route failures.
TEST_VALIDITY: login chooser valid; downstream Phone-form hypothesis remained inconclusive.

Run 37417529886 used an exact-label matcher and reported PHONE_CONTROL_VISIBLE=0 although the chooser accessibility text contained Facebook | Phone. The matcher was widened.

Run 37417842391 then found PHONE_CONTROL_COUNT=1 and tapped the Phone-bearing node, but the immediate post-navigation UIAutomator dump was transiently unavailable and /tmp/phone-form.xml did not exist. This is a harness observation failure, not evidence that the Phone route failed.

Current repair adds bounded UI dump retries after authentication navigation. Next valid signal must include a successful post-tap dump before classifying the Phone form.
