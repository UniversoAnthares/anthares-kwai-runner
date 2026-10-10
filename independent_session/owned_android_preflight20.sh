#!/usr/bin/env bash
set -euo pipefail
export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$PATH"
pass=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "CHECK_OK:$label"; else echo "CHECK_FAIL:$label"; return 1; fi
  pass=$((pass+1))
}
check 01-linux test "$(uname -s)" = Linux
check 02-x64 test "$(uname -m)" = x86_64
check 03-sdk-root test -d "$ANDROID_HOME"
check 04-cmdline test -d "$ANDROID_HOME/cmdline-tools"
check 05-sdkmanager command -v sdkmanager
check 06-avdmanager command -v avdmanager
check 07-adb command -v adb
check 08-java command -v java
check 09-python command -v python3
check 10-tar command -v tar
check 11-unzip command -v unzip
check 12-curl command -v curl
check 13-kvm-node test -e /dev/kvm
check 14-kvm-read test -r /dev/kvm
check 15-kvm-write test -w /dev/kvm
check 16-cpu-vmx-svm bash -c "grep -Eq '(vmx|svm)' /proc/cpuinfo"
check 17-free-disk bash -c '[ "$(df -Pk "$1" | awk "NR==2 {print \$4}")" -gt 4000000 ]' _ "$RUNNER_TEMP"
check 18-free-memory bash -c '[ "$(awk "/MemAvailable:/ {print \$2}" /proc/meminfo)" -gt 3000000 ]'
check 19-sdkmanager-version bash -c "timeout 10s sdkmanager --version"
check 20-emulator-package bash -c "test -d '$ANDROID_HOME/emulator' || command -v sdkmanager >/dev/null"
echo "PREFLIGHT_20_CHECKS_PASSED=$pass"
