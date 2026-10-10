#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  1) adb shell pm path com.kwai.video | grep -q package: ;;
  2) adb shell pm list packages | grep -qx 'package:com.kwai.video' ;;
  3) adb shell dumpsys package com.kwai.video | grep -q 'Package \[com.kwai.video\]' ;;
  4) adb shell dumpsys package com.kwai.video | grep -q 'versionCode=' ;;
  5) adb shell dumpsys package com.kwai.video | grep -q 'versionName=' ;;
  6) adb shell dumpsys package com.kwai.video | grep -q 'targetSdk=' ;;
  7) adb shell dumpsys package com.kwai.video | grep -q 'firstInstallTime=' ;;
  8) adb shell dumpsys package com.kwai.video | grep -q 'lastUpdateTime=' ;;
  9) adb shell pm path com.kwai.video | grep -q '/data/app/' ;;
  10) adb shell dumpsys package com.kwai.video | grep -q 'codePath=' ;;
  11) adb shell dumpsys package com.kwai.video | grep -q 'resourcePath=' ;;
  12) adb shell dumpsys package com.kwai.video | grep -q 'userId=' ;;
  13) adb shell dumpsys package com.kwai.video | grep -q 'pkgFlags=' ;;
  14) adb shell dumpsys package com.kwai.video | grep -q 'User 0:' ;;
  15) adb shell dumpsys activity activities | grep -E 'com.kwai.video|mResumedActivity|topResumedActivity' ;;
  16) adb shell pidof com.kwai.video ;;
  17) adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 | grep -q 'Events injected: 1' ;;
  18) test -s /tmp/anthares-stage4/screenshot.png ;;
  19) grep -q STEP_INSTALL_MULTIPLE_OK /tmp/anthares-stage4/install.txt ;;
  20) grep -q KWAI_LAUNCHED /tmp/anthares-stage4/install.txt ;;
  21) test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1 ;;
  22) test "$(adb shell getprop ro.product.cpu.abi | tr -d '\r')" = x86_64 ;;
  23) adb shell wm size | grep -Eq '[0-9]+x[0-9]+' ;;
  24) adb shell wm density | grep -Eq '[0-9]+' ;;
  25) adb shell pm list packages -3 | grep -qx 'package:com.kwai.video' ;;
  26) adb shell dumpsys package com.kwai.video | grep -q 'android.permission.INTERNET' ;;
  27) adb shell dumpsys package com.kwai.video | grep -q 'android.intent.action.MAIN' ;;
  28) adb shell logcat -d -t 300 | grep -Eqi 'com.kwai.video|kwai' ;;
  29) test -s /tmp/anthares-stage4/kwai-vault.zip && unzip -t /tmp/anthares-stage4/kwai-vault.zip >/dev/null ;;
  30) test "$(find kwai-vault -maxdepth 1 -type f -name '*.apk' | wc -l)" -gt 1 ;;
  *) exit 2 ;;
esac
echo "STAGE4_DIAGNOSTIC_${1}_PASS"
