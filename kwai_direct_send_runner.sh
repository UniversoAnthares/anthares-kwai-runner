#!/usr/bin/env bash
set -Eeuo pipefail

bash kwai_vault_install.sh
adb shell monkey -p com.kwai.video 1
sleep 7
python3 kwai_state_driver.py | tee direct-send-fsm.log
grep -q 'FSM_MAIN_REACHED' direct-send-fsm.log || {
  echo 'TEST_VALIDITY=NO_FSM_MAIN'
  exit 90
}
echo 'TEST_VALIDITY=FSM_MAIN_REACHED'

set +e
python3 kwai_direct_send_probe.py | tee direct-send-probe.log
rc=${PIPESTATUS[0]}
set -e
echo "DIRECT_SEND_PROBE_RC=$rc"
exit "$rc"
