#!/usr/bin/env bash
set -Eeuo pipefail
mode="${1:-cold}"
bash kwai_vault_install.sh
adb logcat -c || true
adb shell am force-stop com.kwai.video || true
case "$mode" in
  fresh-data) adb shell pm clear com.kwai.video ;;
  clear-cache) adb shell pm trim-caches 999G || true ;;
  permission) adb shell pm grant com.kwai.video android.permission.POST_NOTIFICATIONS || true ;;
esac
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 || true
case "$mode" in
  wait45) sleep 45 ;;
  wait15) sleep 15 ;;
  warm|relaunch) sleep 8; adb shell am force-stop com.kwai.video; adb shell monkey -p com.kwai.video 1; sleep 10 ;;
  *) sleep 12 ;;
esac
adb shell uiautomator dump /sdcard/final.xml || true
adb exec-out cat /sdcard/final.xml > final.xml || true
adb shell getprop ro.product.cpu.abilist > device-abi.txt
adb shell pm path com.kwai.video > package-paths.txt || true
adb shell dumpsys activity activities > final-activities.txt
adb shell pidof com.kwai.video > kwai-pid.txt || true
adb logcat -d -v brief | grep -Ei 'com.kwai.video|AndroidRuntime|FATAL EXCEPTION|UnsatisfiedLinkError|SIGSEGV|dlopen|ANR' | tail -120 > kwai-launch-events.txt || true
adb logcat -b crash -d -v brief > kwai-crash-log.txt || true
adb shell dumpsys meminfo com.kwai.video > kwai-meminfo.txt || true
echo "CASE=$mode"
if test -s kwai-pid.txt && grep -Eq 'com.kwai.video/' final-activities.txt; then
  echo KWAI_FOREGROUND_AUTH_GATE=PASS
else
  echo KWAI_FOREGROUND_AUTH_GATE=FAIL
  exit 31
fi
