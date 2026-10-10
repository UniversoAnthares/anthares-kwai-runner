#!/usr/bin/env bash
# Twenty distinct concurrent, bounded diagnostics on GitHub-hosted Linux.
set -Eeuo pipefail
case "${1:?case}" in
  01) uname -a ;;
  02) test -e /dev/kvm && ls -l /dev/kvm ;;
  03) grep -E 'vmx|svm' /proc/cpuinfo | head -1 ;;
  04) command -v sdkmanager ;;
  05) sdkmanager --version ;;
  06) command -v avdmanager ;;
  07) command -v emulator ;;
  08) emulator -version | head -5 ;;
  09) command -v adb ;;
  10) adb version ;;
  11) df -h "$HOME" ;;
  12) free -h ;;
  13) nproc ;;
  14) env | grep -E '^(ANDROID_HOME|ANDROID_SDK_ROOT|JAVA_HOME)=' ;;
  15) java -version ;;
  16) ls -ld "${ANDROID_HOME:-/usr/local/lib/android/sdk}" ;;
  17) ls -l "${ANDROID_HOME:-/usr/local/lib/android/sdk}/system-images/android-35/google_apis/x86_64" ;;
  18) ls -l "${ANDROID_HOME:-/usr/local/lib/android/sdk}/emulator/emulator" ;;
  19) test -w "${RUNNER_TEMP:-/tmp}" ;;
  20) python3 -m py_compile independent_android/preflight.py ;;
  *) exit 2 ;;
esac
echo "ANTHARES_DIAG_CASE_${1}=PASS"
