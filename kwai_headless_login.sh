#!/usr/bin/env bash
set -Eeuo pipefail
REPORT="kwai-headless-status.txt"
SHOT="kwai-headless-ready.png"
: >"$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }
capture(){ adb exec-out screencap -p >"$SHOT" 2>/dev/null || true; }
trap capture EXIT
adb wait-for-device
for _ in $(seq 1 45); do
  [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && break
  sleep 2
done
[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] || { log "FAIL: android-not-ready"; exit 21; }
log "ANDROID_READY"
if ! adb shell pm path com.kwai.video 2>/dev/null | grep -q package:; then
  test -s kwai-vault/MANIFEST.tsv || { log "FAIL: validated-vault-missing"; exit 29; }
  bash kwai_vault_install.sh >>"$REPORT" 2>&1 || { log "FAIL: validated-vault-install"; exit 30; }
fi
log "KWAI_INSTALLED"
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >>"$REPORT" 2>&1 || { log "FAIL: kwai-launch"; exit 31; }
for _ in $(seq 1 15); do
  adb shell uiautomator dump /sdcard/kwai-ui.xml >/dev/null 2>&1 || true
  adb pull /sdcard/kwai-ui.xml /tmp/kwai-ui.xml >/dev/null 2>&1 || true
  if [ -s /tmp/kwai-ui.xml ] && grep -Eq 'text="[^"]+"|content-desc="[^"]+"' /tmp/kwai-ui.xml && ! grep -qi 'Make Everyone Shine' /tmp/kwai-ui.xml; then
    log "KWAI_UI_INTERACTIVE"; break
  fi
  sleep 2
done
test -s /tmp/kwai-ui.xml || { log "FAIL: no-ui-dump"; exit 32; }
log "KWAI_AUTO_LOGIN_ATTEMPT"
if ! python3 kwai_android_autologin.py >>"$REPORT" 2>&1; then
  rc=$?; log "KWAI_AUTO_LOGIN_FALLBACK_REQUIRED_RC=$rc"; exit 60
fi
log "KWAI_AUTO_LOGIN_ADVANCED"
for _ in $(seq 1 15); do
  sleep 2
  adb shell uiautomator dump /sdcard/kwai-ui.xml >/dev/null 2>&1 || true
  adb pull /sdcard/kwai-ui.xml /tmp/kwai-ui.xml >/dev/null 2>&1 || true
  ui="$(tr '[:upper:]' '[:lower:]' </tmp/kwai-ui.xml 2>/dev/null || true)"
  if echo "$ui" | grep -Eqi 'verification code|código de verificação|captcha|verify it.s you|senha|password|log in|login|entrar'; then
    continue
  fi
  if echo "$ui" | grep -Eqi 'profile|perfil|following|seguindo|for you|para você|discover|descobrir|friends|amigos'; then
    log "KWAI_SESSION_AUTHENTICATED"
    adb shell pidof com.kwai.video >/dev/null || { log "FAIL: kwai-process-missing"; exit 62; }
    log "KWAI_HEALTH_OK"
    exit 0
  fi
done
log "KWAI_SESSION_UNCONFIRMED"
exit 61
