#!/usr/bin/env bash
# Save/restore a complete Android AVD with sealed state in independent cloud jobs.
# This file never exports a Google password, cookies or AVD plaintext artifacts.
set -Eeuo pipefail
mode="${1:?use capture or restore}"
archive="${2:?path to sealed archive}"
SDK="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
ADB="$SDK/platform-tools/adb"
EMU="$SDK/emulator/emulator"
AVD_ROOT="$HOME/.android"
PROFILE=tiktok-persist
SNAPSHOT=tiktok-ready
script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/tiktok_avd_sealed_state.py"
export ANDROID_SDK_HOME="$HOME"
export ANDROID_AVD_HOME="$AVD_ROOT/avd"

preflight(){
  command -v python3 >/dev/null
  command -v tar >/dev/null
  command -v zstd >/dev/null
  test -x "$ADB" && test -x "$EMU"
  test -n "${ANTHARES_BROWSER_STATE_KEY:-}" || { echo TIKTOK_CHECKPOINT_KEY_ABSENT=1; exit 2; }
}
preflight
case "$mode" in
capture)
  test -d "$AVD_ROOT/avd/$PROFILE.avd" && test -s "$AVD_ROOT/avd/$PROFILE.ini"
  state="$("$ADB" -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')"
  test "$state" = 1 || { echo TIKTOK_CHECKPOINT_EMULATOR_NOT_READY=1; exit 3; }
  # One snapshot at a time, single profile, after stopping any media uploader.
  timeout 120 "$ADB" -s emulator-5554 emu avd snapshot save "$SNAPSHOT" >/dev/null
  test -d "$AVD_ROOT/avd/$PROFILE.avd/snapshots/$SNAPSHOT" || { echo TIKTOK_CHECKPOINT_SNAPSHOT_MISSING=1; exit 4; }
  "$ADB" -s emulator-5554 emu kill >/dev/null || true
  for i in $(seq 1 50); do
    "$ADB" -s emulator-5554 get-state >/dev/null 2>&1 || break
    sleep 1
  done
  if "$ADB" -s emulator-5554 get-state >/dev/null 2>&1; then echo TIKTOK_CHECKPOINT_EMULATOR_STILL_RUNNING=1;exit 5;fi
  sync
  python3 "$script" seal --root "$AVD_ROOT" --archive "$archive"
  test -s "$archive"
  echo TIKTOK_CHECKPOINT_ENCRYPTED_READY=1
  ;;
restore)
  test -r "$archive" || { echo TIKTOK_CHECKPOINT_ENCRYPTED_ARCHIVE_MISSING=1; exit 6; }
  if [ -e "$AVD_ROOT/avd/$PROFILE.avd" ];then
    echo TIKTOK_CHECKPOINT_REFUSE_OVERWRITE_EXISTING_AVD=1
    exit 7
  fi
  mkdir -p "$AVD_ROOT"
  python3 "$script" restore --root "$AVD_ROOT" --archive "$archive"
  test -d "$AVD_ROOT/avd/$PROFILE.avd/snapshots/$SNAPSHOT" || { echo TIKTOK_CHECKPOINT_RESTORED_SNAPSHOT_MISSING=1;exit 8; }
  if [ ! -e /dev/kvm ];then echo TIKTOK_CHECKPOINT_KVM_ABSENT=1;exit 9;fi
  sudo chmod 666 /dev/kvm
  nohup "$EMU" -avd "$PROFILE" -snapshot "$SNAPSHOT" -no-snapshot-save \
    -no-window -no-audio -no-boot-anim -gpu swiftshader_indirect \
    -accel on -memory 2048 -cores 2 -port 5554 >/tmp/tiktok-avd-restore-emulator.log 2>&1 &
  timeout 120 "$ADB" -s emulator-5554 wait-for-device
  timeout 160 bash -c 'until [ "$("$1" -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")" = 1 ]; do sleep 1; done' _ "$ADB"
  if grep -q "Successfully loaded snapshot '$SNAPSHOT'" /tmp/tiktok-avd-restore-emulator.log && \
     ! grep -Eq "Failed to load snapshot|performing a cold boot" /tmp/tiktok-avd-restore-emulator.log;then
    echo TIKTOK_CHECKPOINT_SNAPSHOT_ACTUAL_LOAD=1
  else
    echo TIKTOK_CHECKPOINT_SNAPSHOT_ACTUAL_LOAD=0
    exit 10
  fi
  echo TIKTOK_CHECKPOINT_ANDROID_RESTORED=1
  ;;
*)
  echo TIKTOK_CHECKPOINT_INVALID_MODE=1;exit 11
  ;;
esac
