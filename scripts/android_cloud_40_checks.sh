#!/usr/bin/env bash
set -uo pipefail
phase="${1:-all}"
passed=0; failed=0
check() { local name="$1" cmd="$2"; if bash -o pipefail -c "$cmd" >/dev/null 2>&1; then echo "PASS $name"; passed=$((passed+1)); else echo "FAIL $name"; failed=$((failed+1)); fi; }
if [[ "$phase" == host || "$phase" == all ]]; then
check "01_python" 'command -v python3'
check "02_bash" 'command -v bash'
check "03_java" 'command -v java'
check "04_sdkroot" 'test -d "$ANDROID_SDK_ROOT"'
check "05_sdkmanager" 'test -x "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"'
check "06_avdmanager" 'test -x "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/avdmanager"'
check "07_adb_binary" 'test -x "$ANDROID_SDK_ROOT/platform-tools/adb"'
check "08_emulator_binary" 'test -x "$ANDROID_SDK_ROOT/emulator/emulator"'
check "09_kvm_device" 'test -e /dev/kvm'
check "10_kvm_readable" 'test -r /dev/kvm'
check "11_kvm_writable" 'test -w /dev/kvm'
check "12_disk" 'test "$(df -Pk . | awk '\''END {print $4}'\'')" -gt 1048576'
check "13_memory" 'test "$(awk '\''/MemTotal/ {print $2}'\'' /proc/meminfo)" -gt 2097152'
check "14_arch" 'test "$(uname -m)" = x86_64'
check "15_adb_version" '"$ANDROID_SDK_ROOT/platform-tools/adb" version >/dev/null'
check "16_emulator_version" '"$ANDROID_SDK_ROOT/emulator/emulator" -version >/dev/null 2>&1'
check "17_avd_present" '"$ANDROID_SDK_ROOT/emulator/emulator" -list-avds | grep -Fx anthares-cloud'
check "18_avd_config" 'test -f "$HOME/.android/avd/anthares-cloud.avd/config.ini"'
check "19_system_image" 'test -d "$ANDROID_SDK_ROOT/system-images/android-30/google_apis/x86_64"'
check "20_adb_server" '"$ANDROID_SDK_ROOT/platform-tools/adb" start-server >/dev/null'
fi
if [[ "$phase" == device || "$phase" == all ]]; then
check "21_device_list" 'adb devices | grep -q '\''emulator-.*device'\'''
check "22_boot" 'test "$(adb shell getprop sys.boot_completed | tr -d '\''\r'\'')" = 1'
check "23_sdk" 'test "$(adb shell getprop ro.build.version.sdk | tr -d '\''\r'\'')" = 30'
check "24_release" 'test -n "$(adb shell getprop ro.build.version.release)"'
check "25_abi" 'adb shell getprop ro.product.cpu.abi | grep -q x86_64'
check "26_shell" 'adb shell '\''echo ready'\'' | grep -q ready'
check "27_packages" 'adb shell pm list packages | grep -q package:'
check "28_activity" 'adb shell cmd activity help >/dev/null'
check "29_package_manager" 'adb shell pm help >/dev/null'
check "30_data" 'adb shell '\''test -d /data'\'''
check "31_sdcard" 'adb shell '\''test -d /sdcard'\'''
check "32_system" 'adb shell '\''test -d /system'\'''
check "33_proc" 'adb shell '\''test -d /proc'\'''
check "34_serial" 'test -n "$(adb get-serialno)"'
check "35_state" 'test "$(adb get-state | tr -d '\''\r'\'')" = device'
check "36_uptime" 'adb shell cat /proc/uptime | grep -Eq '\''^[0-9]+'\'''
check "37_manufacturer" 'test -n "$(adb shell getprop ro.product.manufacturer)"'
check "38_model" 'test -n "$(adb shell getprop ro.product.model)"'
check "39_display" 'adb shell wm size | grep -q '\''Physical size'\'''
check "40_density" 'adb shell wm density | grep -q '\''Physical density'\'''
fi
echo "DIAGNOSTIC_RESULT phase=$phase passed=$passed failed=$failed"
test "$failed" -eq 0
