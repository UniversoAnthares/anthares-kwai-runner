#!/usr/bin/env bash
set -Eeuo pipefail

BUNDLE="${1:?usage: x_install_apkm_bundle.sh /path/to/x.apkm}"
OUT_DIR="${X_APK_DIR:-/tmp/x-apks}"
EXPECTED_CERT_SHA256="${X_CERT_SHA256:-0fd9a0cfb07b65950997b4eaebdc53931392391aa406538a3b04073bc2ce2fe9}"

command -v unzip >/dev/null 2>&1 || { echo 'unzip is required' >&2; exit 2; }
command -v adb >/dev/null 2>&1 || { echo 'adb is required' >&2; exit 2; }
[[ -s "$BUNDLE" ]] || { echo "bundle missing: $BUNDLE" >&2; exit 2; }

SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
resolve_build_tool() {
  local tool="$1" found=""
  if command -v "$tool" >/dev/null 2>&1; then
    command -v "$tool"
    return 0
  fi
  if [[ -n "$SDK_ROOT" && -d "$SDK_ROOT/build-tools" ]]; then
    found="$(find "$SDK_ROOT/build-tools" -mindepth 2 -maxdepth 2 -type f -name "$tool" -print | sort -V | tail -1)"
  fi
  [[ -n "$found" ]] || return 1
  printf '%s\n' "$found"
}

AAPT="$(resolve_build_tool aapt)" || { echo 'aapt is required' >&2; exit 2; }
APKSIGNER="$(resolve_build_tool apksigner)" || { echo 'apksigner is required' >&2; exit 2; }

echo "ANDROID_BUILD_TOOLS aapt=$AAPT apksigner=$APKSIGNER"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
unzip -q "$BUNDLE" -d "$OUT_DIR"

mapfile -t APKS < <(find "$OUT_DIR" -type f -name '*.apk' -print | sort)
((${#APKS[@]} > 0)) || { echo 'no APKs found in bundle' >&2; exit 3; }

BASE=""
for apk in "${APKS[@]}"; do
  pkg="$($AAPT dump badging "$apk" 2>/dev/null | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -1)"
  [[ "$pkg" == 'com.twitter.android' ]] || { echo "unexpected package in $(basename "$apk"): $pkg" >&2; exit 4; }

  cert="$($APKSIGNER verify --print-certs "$apk" 2>/dev/null | sed -n 's/^Signer #1 certificate SHA-256 digest: //p' | head -1 | tr '[:upper:]' '[:lower:]' | tr -d ':[:space:]')"
  [[ "$cert" == "$EXPECTED_CERT_SHA256" ]] || {
    echo "X signing certificate mismatch in $(basename "$apk")" >&2
    echo "expected=$EXPECTED_CERT_SHA256 actual=$cert" >&2
    exit 5
  }

  if $AAPT dump badging "$apk" 2>/dev/null | grep -q "application-label"; then
    if [[ -z "$BASE" ]] && [[ "$(basename "$apk")" =~ ^base\.apk$|^com\.twitter\.android.*\.apk$ ]]; then
      BASE="$apk"
    fi
  fi
done

set +e
adb install-multiple -r -d "${APKS[@]}"
rc=$?
set -e

if ((rc != 0)); then
  [[ -n "$BASE" ]] || BASE="$(find "$OUT_DIR" -type f -name 'base.apk' -print -quit)"
  [[ -n "$BASE" ]] || { echo 'unable to locate base APK for filtered retry' >&2; exit 6; }

  DENSITY="$(adb shell wm density 2>/dev/null | sed -n 's/.*: //p' | head -1 | tr -d '\r')"
  case "${DENSITY:-420}" in
    ''|*[!0-9]*) DENSITY=420 ;;
  esac
  SELECTED=("$BASE")
  for apk in "${APKS[@]}"; do
    [[ "$apk" == "$BASE" ]] && continue
    name="$(basename "$apk" | tr '[:upper:]' '[:lower:]')"
    case "$name" in
      *arm64*|*aarch64*|*config.en*|*config.pt*|*config.xxhdpi*|*config.420*|*master*|*base*) SELECTED+=("$apk") ;;
    esac
  done
  adb install-multiple -r -d "${SELECTED[@]}"
fi

adb shell pm path com.twitter.android >/dev/null
version="$(adb shell dumpsys package com.twitter.android | sed -n 's/.*versionName=//p' | head -1 | tr -d '\r')"
echo "X_APK_INSTALL_OK package=com.twitter.android version=${version:-unknown} cert=$EXPECTED_CERT_SHA256"
