#!/usr/bin/env bash
set -Eeuo pipefail

OUT="${X_APK_OUT:-/tmp/xout}"
EVIDENCE="${X_APK_EVIDENCE:-evidence/apk-verify}"
OFFICIAL_SHA256="0fd9a0cfb07b65950997b4eaebdc53931392391aa406538a3b04073bc2ce2fe9"
mkdir -p "$EVIDENCE"
mapfile -t APKS < <(find "$OUT" -type f -name '*.apk' -print | sort)
((${#APKS[@]} > 0)) || { echo NO_APKS_TO_VERIFY | tee "$EVIDENCE/verdict.txt"; exit 70; }

SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
BT=""
if [[ -n "$SDK_ROOT" && -d "$SDK_ROOT/build-tools" ]]; then
  BT="$(find "$SDK_ROOT/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
fi
AAPT="${BT:+$BT/aapt}"
APKSIGNER="${BT:+$BT/apksigner}"
if [[ ! -x "$AAPT" || ! -x "$APKSIGNER" ]]; then
  yes | sdkmanager 'build-tools;35.0.0' >/dev/null
  BT="$SDK_ROOT/build-tools/35.0.0"
  AAPT="$BT/aapt"
  APKSIGNER="$BT/apksigner"
fi

: > "$EVIDENCE/verification.txt"
for apk in "${APKS[@]}"; do
  base="$(basename "$apk")"
  "$AAPT" dump badging "$apk" > "$EVIDENCE/badging-$base.txt" 2>&1
  pkg="$(sed -n "s/^package: name='\([^']*\)'.*/\1/p" "$EVIDENCE/badging-$base.txt" | head -1)"
  [[ "$pkg" == "com.twitter.android" ]] || { echo "WRONG_PACKAGE:$base:$pkg" | tee "$EVIDENCE/verdict.txt"; exit 71; }
  "$APKSIGNER" verify --verbose --print-certs "$apk" > "$EVIDENCE/apksigner-$base.txt" 2>&1
  grep -Eqi "certificate SHA-256 digest:[[:space:]]*$OFFICIAL_SHA256([[:space:]]|$)" "$EVIDENCE/apksigner-$base.txt" \
    || { echo "OFFICIAL_CERT_NOT_CONFIRMED:$base" | tee "$EVIDENCE/verdict.txt"; exit 73; }
  printf '%s package=%s signer=%s\n' "$base" "$pkg" "$OFFICIAL_SHA256" >> "$EVIDENCE/verification.txt"
done
printf 'apk_count=%s\n' "${#APKS[@]}" | tee "$EVIDENCE/apk-count.txt"
echo VERIFIED_OFFICIAL_X_APK | tee "$EVIDENCE/verdict.txt"
