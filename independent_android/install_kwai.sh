#!/usr/bin/env bash
# Anthares-owned APK acquisition and verified multi-split installation.
set -Eeuo pipefail
VAULT_URL="https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/kwai-package-vault/kwai-vault.zip"
VAULT_SHA256="96650454576a2cf5cc5e63d90011f0b60a03d2702605756f40cc934cd6ae5543"
test "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1
curl --fail --location --retry 3 --connect-timeout 10 --max-time 180 --silent --show-error --output kwai-vault.zip "$VAULT_URL"
printf '%s  %s\n' "$VAULT_SHA256" kwai-vault.zip | sha256sum --check --status
mkdir -p kwai-vault
unzip -oq kwai-vault.zip -d kwai-vault
bash kwai_vault_install.sh
test -n "$(adb shell pm path com.kwai.video)"
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 5
FOREGROUND="$(adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity' | head -3 || true)"
if ! grep -q 'com.kwai.video' <<<"$FOREGROUND"; then
  echo ANTHARES_KWAI_FOREGROUND_NOT_VERIFIED=1
  exit 7
fi
echo ANTHARES_KWAI_INSTALLED_AND_FOREGROUND=PASS
