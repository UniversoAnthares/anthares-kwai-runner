# Kwai launcher-ANR autologin replacement
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37456128589
SUPERSEDES: test-hub/findings/20261006-1150-lease-kwai-state-driven-auth-recovery.md

Run 37455005102 proved credentials present and Kwai launch, but the credential hypothesis was not validly tested: UI was Pixel Launcher ANR and AUTOLOGIN_FAILED_RC=3. Separately, run 37454956004 proved the state-driven runtime reaches FSM_MAIN_REACHED and LOGIN_SURFACE_REACHED.

Causal replacement: kwai_acceptance.sh now requires kwai_state_driver.py + FSM_MAIN_REACHED before any credential attempt. The real credential workflow is serialized to one attempt; 30 simultaneous credential submissions are explicitly avoided to prevent account lockout/challenge amplification. Current serialized acceptance is queued.
