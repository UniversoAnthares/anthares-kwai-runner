#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  1) adb get-state | grep -qx device ;;
  2) test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1 ;;
  3) test "$(adb shell getprop ro.build.version.sdk | tr -d '\r')" = 30 ;;
  4) test -n "$(adb shell getprop ro.build.version.release)" ;;
  5) test -n "$(adb shell getprop ro.product.cpu.abi)" ;;
  6) adb shell echo READY | grep -qx READY ;;
  7) adb shell pm path android | grep -q package: ;;
  8) adb shell cmd activity help >/dev/null ;;
  9) adb shell pm help >/dev/null ;;
  10) adb shell test -d /system ;;
  11) adb shell test -d /data ;;
  12) adb shell test -d /proc ;;
  13) test "$(adb get-serialno)" != unknown ;;
  14) adb shell cat /proc/uptime | grep -Eq '^[0-9]+' ;;
  15) test -n "$(adb shell getprop ro.product.manufacturer)" ;;
  16) test -n "$(adb shell getprop ro.product.model)" ;;
  17) adb shell wm size | grep -q 'Physical size' ;;
  18) adb shell wm density | grep -q 'Physical density' ;;
  19) test -n "$(adb shell getprop ro.build.fingerprint)" ;;
  20) test "$(adb shell getprop ro.kernel.qemu | tr -d '\r')" = 1 ;;
  *) echo 'Invalid matrix check' >&2; exit 2 ;;
esac
echo "MATRIX_CHECK_${1}_PASS"
