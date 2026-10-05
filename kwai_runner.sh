#!/usr/bin/env bash
set -euo pipefail

: "${KWAI_LOGIN:?KWAI_LOGIN is required}"
: "${KWAI_PASSWORD:?KWAI_PASSWORD is required}"

adb wait-for-device
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

# The actual package is supplied separately after validation.
test -f "${KWAI_PACKAGE:-/dev/null}" || {
  echo "Validated Kwai package was not supplied"
  exit 20
}

adb install-multiple -r "${KWAI_PACKAGE}" || adb install -r "${KWAI_PACKAGE}"

adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true

echo "KWAI_RUNNER_ANDROID_READY"
