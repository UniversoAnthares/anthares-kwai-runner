#!/usr/bin/env bash
set -Eeuo pipefail

: "${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID is required}"
: "${FIREBASE_TEST_MODEL:?FIREBASE_TEST_MODEL is required}"
: "${FIREBASE_TEST_VERSION:?FIREBASE_TEST_VERSION is required}"
command -v gcloud >/dev/null
command -v unzip >/dev/null

VAULT_URL="${KWAI_VAULT_URL:-https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/kwai-package-vault/kwai-vault.zip}"
VAULT_SHA="${KWAI_VAULT_SHA256:-96650454576a2cf5cc5e63d90011f0b60a03d2702605756f40cc934cd6ae5543}"
curl -fL --retry 5 --retry-all-errors --connect-timeout 15 --max-time 180 -o kwai-vault.zip "$VAULT_URL"
echo "$VAULT_SHA  kwai-vault.zip" | sha256sum -c -
rm -rf kwai-vault && mkdir kwai-vault
unzip -q kwai-vault.zip -d kwai-vault
BASE="$(find kwai-vault -type f -name 'com.kwai.video.apk' -print -quit)"
[ -n "$BASE" ] || BASE="$(find kwai-vault -type f -name 'base.apk' -print -quit)"
[ -n "$BASE" ] || { echo FIREBASE_FTL_NO_BASE_APK; exit 40; }
mapfile -t EXTRA < <(find kwai-vault -type f -name '*.apk' ! -path "$BASE" | sort)
[ "${#EXTRA[@]}" -gt 0 ] || { echo FIREBASE_FTL_NO_SPLITS; exit 41; }
ADDITIONAL="$(IFS=,; echo "${EXTRA[*]}")"
echo "FIREBASE_FTL_MODEL=$FIREBASE_TEST_MODEL"
echo "FIREBASE_FTL_VERSION=$FIREBASE_TEST_VERSION"
echo "FIREBASE_FTL_SPLIT_COUNT=${#EXTRA[@]}"
gcloud firebase test android run --project "$FIREBASE_PROJECT_ID" --type robo --app "$BASE" --additional-apks "$ADDITIONAL" --device "model=${FIREBASE_TEST_MODEL},version=${FIREBASE_TEST_VERSION},locale=en,orientation=portrait" --timeout 10m --results-history-name anthares-kwai-fallback --no-auto-google-login
echo FIREBASE_FTL_KWAI_MATRIX=PASS
