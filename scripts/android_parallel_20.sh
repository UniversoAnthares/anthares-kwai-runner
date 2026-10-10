#!/usr/bin/env bash
set -euo pipefail
mkdir -p /tmp/anthares-parallel-checks
pids=()
names=()
( timeout 35 bash -c "adb get-state | tr -d '\\r' | grep -x device" > /tmp/anthares-parallel-checks/01_adb_connected.log 2>&1; echo $? > /tmp/anthares-parallel-checks/01_adb_connected.rc ) &
pids+=("$!"); names+=("01_adb_connected")
( timeout 35 bash -c "test \"$(adb shell getprop sys.boot_completed | tr -d '\\r')\" = 1" > /tmp/anthares-parallel-checks/02_android_boot.log 2>&1; echo $? > /tmp/anthares-parallel-checks/02_android_boot.rc ) &
pids+=("$!"); names+=("02_android_boot")
( timeout 35 bash -c "test \"$(adb shell getprop ro.build.version.sdk | tr -d '\\r')\" = 30" > /tmp/anthares-parallel-checks/03_api_30.log 2>&1; echo $? > /tmp/anthares-parallel-checks/03_api_30.rc ) &
pids+=("$!"); names+=("03_api_30")
( timeout 35 bash -c "test -n \"$(adb shell getprop ro.build.version.release)\"" > /tmp/anthares-parallel-checks/04_android_release.log 2>&1; echo $? > /tmp/anthares-parallel-checks/04_android_release.rc ) &
pids+=("$!"); names+=("04_android_release")
( timeout 35 bash -c "test -n \"$(adb shell getprop ro.product.cpu.abi)\"" > /tmp/anthares-parallel-checks/05_cpu_abi.log 2>&1; echo $? > /tmp/anthares-parallel-checks/05_cpu_abi.rc ) &
pids+=("$!"); names+=("05_cpu_abi")
( timeout 35 bash -c "test \"$(adb shell echo ready | tr -d '\\r')\" = ready" > /tmp/anthares-parallel-checks/06_shell_ready.log 2>&1; echo $? > /tmp/anthares-parallel-checks/06_shell_ready.rc ) &
pids+=("$!"); names+=("06_shell_ready")
( timeout 35 bash -c "adb shell pm path android | grep -m1 -F package:" > /tmp/anthares-parallel-checks/07_package_manager.log 2>&1; echo $? > /tmp/anthares-parallel-checks/07_package_manager.rc ) &
pids+=("$!"); names+=("07_package_manager")
( timeout 35 bash -c "adb shell cmd activity help >/dev/null" > /tmp/anthares-parallel-checks/08_activity_manager.log 2>&1; echo $? > /tmp/anthares-parallel-checks/08_activity_manager.rc ) &
pids+=("$!"); names+=("08_activity_manager")
( timeout 35 bash -c "adb shell pm help >/dev/null" > /tmp/anthares-parallel-checks/09_pm_help.log 2>&1; echo $? > /tmp/anthares-parallel-checks/09_pm_help.rc ) &
pids+=("$!"); names+=("09_pm_help")
( timeout 35 bash -c "adb shell 'test -d /system'" > /tmp/anthares-parallel-checks/10_system_mount.log 2>&1; echo $? > /tmp/anthares-parallel-checks/10_system_mount.rc ) &
pids+=("$!"); names+=("10_system_mount")
( timeout 35 bash -c "adb shell 'test -d /data'" > /tmp/anthares-parallel-checks/11_data_mount.log 2>&1; echo $? > /tmp/anthares-parallel-checks/11_data_mount.rc ) &
pids+=("$!"); names+=("11_data_mount")
( timeout 35 bash -c "adb shell 'test -d /proc'" > /tmp/anthares-parallel-checks/12_proc_mount.log 2>&1; echo $? > /tmp/anthares-parallel-checks/12_proc_mount.rc ) &
pids+=("$!"); names+=("12_proc_mount")
( timeout 35 bash -c "test \"$(adb get-serialno)\" != unknown" > /tmp/anthares-parallel-checks/13_serial.log 2>&1; echo $? > /tmp/anthares-parallel-checks/13_serial.rc ) &
pids+=("$!"); names+=("13_serial")
( timeout 35 bash -c "adb shell cat /proc/uptime | grep -E '^[0-9]+'" > /tmp/anthares-parallel-checks/14_uptime.log 2>&1; echo $? > /tmp/anthares-parallel-checks/14_uptime.rc ) &
pids+=("$!"); names+=("14_uptime")
( timeout 35 bash -c "test -n \"$(adb shell getprop ro.product.manufacturer)\"" > /tmp/anthares-parallel-checks/15_manufacturer.log 2>&1; echo $? > /tmp/anthares-parallel-checks/15_manufacturer.rc ) &
pids+=("$!"); names+=("15_manufacturer")
( timeout 35 bash -c "test -n \"$(adb shell getprop ro.product.model)\"" > /tmp/anthares-parallel-checks/16_model.log 2>&1; echo $? > /tmp/anthares-parallel-checks/16_model.rc ) &
pids+=("$!"); names+=("16_model")
( timeout 35 bash -c "adb shell wm size | grep -F 'Physical size'" > /tmp/anthares-parallel-checks/17_display_size.log 2>&1; echo $? > /tmp/anthares-parallel-checks/17_display_size.rc ) &
pids+=("$!"); names+=("17_display_size")
( timeout 35 bash -c "adb shell wm density | grep -F 'Physical density'" > /tmp/anthares-parallel-checks/18_display_density.log 2>&1; echo $? > /tmp/anthares-parallel-checks/18_display_density.rc ) &
pids+=("$!"); names+=("18_display_density")
( timeout 35 bash -c "test -n \"$(adb shell getprop ro.build.fingerprint)\"" > /tmp/anthares-parallel-checks/19_build_fingerprint.log 2>&1; echo $? > /tmp/anthares-parallel-checks/19_build_fingerprint.rc ) &
pids+=("$!"); names+=("19_build_fingerprint")
( timeout 35 bash -c "test -n \"$(adb shell getprop ro.kernel.qemu)\"" > /tmp/anthares-parallel-checks/20_emulator_name.log 2>&1; echo $? > /tmp/anthares-parallel-checks/20_emulator_name.rc ) &
pids+=("$!"); names+=("20_emulator_name")
failures=0
for i in "${!pids[@]}"; do
  wait "${pids[$i]}" || true
  name="${names[$i]}"
  rc=$(cat "/tmp/anthares-parallel-checks/$name.rc" 2>/dev/null || echo 99)
  if [[ "$rc" == 0 ]]; then echo "PASS $name"; else echo "FAIL $name rc=$rc"; cat "/tmp/anthares-parallel-checks/$name.log"; failures=$((failures+1)); fi
done
echo "PARALLEL_20_RESULT passed=$((20-failures)) failed=$failures"
exit "$failures"
