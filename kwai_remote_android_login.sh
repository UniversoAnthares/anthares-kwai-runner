#!/usr/bin/env bash
set -Eeuo pipefail
# LATENCY CONTRACT: this workflow is interactive and must fail fast. Never reintroduce
# multi-minute passive waits. Infrastructure phases are capped in seconds; the only
# longer window is explicit human login, and it is bounded so a run cannot sit forever.
# On timeout, preserve diagnostics/cache and resume with a new short run.
REPORT="kwai-remote-status.txt"; SHOT="kwai-remote-ready.png"; : > "$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }
capture(){ adb exec-out screencap -p > "$SHOT" 2>/dev/null || true; }
finish_diag(){ { echo "=== adb ==="; adb devices -l || true; echo "=== package ==="; adb shell pm path com.kwai.video || true; echo "=== foreground ==="; adb shell dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | tail -4 || true; echo "=== tunnel ==="; tail -30 /tmp/tunnel.log 2>/dev/null || true; echo "=== ui ==="; tail -30 /tmp/android-ui.log 2>/dev/null || true; } >> "$REPORT"; capture; }
cleanup(){ finish_diag; [ -n "${UI_PID:-}" ] && kill "$UI_PID" 2>/dev/null || true; [ -n "${TUNNEL_PID:-}" ] && kill "$TUNNEL_PID" 2>/dev/null || true; }
trap cleanup EXIT
adb wait-for-device
for _ in $(seq 1 30); do [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && break; sleep 2; done
[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] || { log "FAIL: android-not-ready"; exit 21; }
log "ANDROID_READY"
python3 kwai_remote_android_ui.py >/tmp/android-ui.log 2>&1 & UI_PID=$!
for _ in $(seq 1 8); do curl -fsS "http://127.0.0.1:8765/?t=${REMOTE_ANDROID_TOKEN}" >/dev/null 2>&1 && break; sleep 1; done
kill -0 "$UI_PID" 2>/dev/null || { log "FAIL: remote-ui-died"; exit 22; }
/tmp/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8765 >/tmp/tunnel.log 2>&1 & TUNNEL_PID=$!
URL=""
for _ in $(seq 1 15); do URL=$(grep -Eo 'https://[-a-z0-9]+\.trycloudflare\.com' /tmp/tunnel.log 2>/dev/null | head -1 || true); [ -n "$URL" ] && break; kill -0 "$TUNNEL_PID" 2>/dev/null || break; sleep 1; done
[ -n "$URL" ] || { log "FAIL: tunnel-url-missing"; exit 23; }
FULL="$URL/?t=$REMOTE_ANDROID_TOKEN"; log "REMOTE_BASE_URL=$URL"
printf '### Kwai Android remoto\n\nAbra o URL-base abaixo e acrescente o token privado somente no navegador. O token não é escrito em logs.\n\n%s\n' "$URL" >> "$GITHUB_STEP_SUMMARY"
if adb shell pm path com.kwai.video 2>/dev/null | grep -q 'package:'; then
  log "KWAI_ALREADY_INSTALLED"
else
  [ -s kwai-vault/MANIFEST.tsv ] || { log "FAIL: validated-vault-missing"; exit 29; }
  bash kwai_vault_install.sh >>"$REPORT" 2>&1 || { log "FAIL: validated-vault-install"; exit 30; }
  log "KWAI_INSTALLED_FROM_VALIDATED_VAULT"
fi
LAUNCH_COMPONENT="$(adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.kwai.video 2>/dev/null | tr -d '\r' | tail -1)"
log "LAUNCH_COMPONENT=$LAUNCH_COMPONENT"
if [ -n "$LAUNCH_COMPONENT" ] && [[ "$LAUNCH_COMPONENT" == com.kwai.video/* ]]; then
  adb shell am start -n "$LAUNCH_COMPONENT" >>"$REPORT" 2>&1 || { log "FAIL: kwai-launch-component"; exit 31; }
else
  adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >>"$REPORT" 2>&1 || { log "FAIL: kwai-launch"; exit 31; }
fi
sleep 2
# A launch is not acceptance. The app must leave the splash and expose a real UI.
for _ in $(seq 1 8); do
  capture
  adb shell uiautomator dump /sdcard/kwai-ui.xml >/dev/null 2>&1 || true
  adb pull /sdcard/kwai-ui.xml /tmp/kwai-ui.xml >/dev/null 2>&1 || true
  if [ -s /tmp/kwai-ui.xml ] && grep -Eq 'text="[^"]+"|content-desc="[^"]+"' /tmp/kwai-ui.xml && ! grep -qi 'Make Everyone Shine' /tmp/kwai-ui.xml; then
    log "KWAI_UI_INTERACTIVE"; break
  fi
  sleep 2
done
if ! grep -Eq 'text="[^"]+"|content-desc="[^"]+"' /tmp/kwai-ui.xml 2>/dev/null; then
  log "FAIL: kwai-stuck-before-interactive-ui"
  adb logcat -d -t 500 2>/dev/null | grep -Ei 'AndroidRuntime|FATAL EXCEPTION|UnsatisfiedLinkError|linker|com\.kwai\.video|gifshow' | tail -120 >>"$REPORT" || true
  exit 32
fi
log "KWAI_LOGIN_UI_OPENED"
# Interactive-first mode: never spend minutes trying credentials before the owner can act.
# The tunnel URL and Kwai UI are available before entering this short interaction window.
log "KWAI_OWNER_INTERACTION_READY"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  printf '\n**KWAI_OWNER_INTERACTION_READY** — use the remote URL shown above.\n' >> "$GITHUB_STEP_SUMMARY"
fi
LOGIN_DEADLINE=$((SECONDS+120))
while [ "$SECONDS" -lt "$LOGIN_DEADLINE" ]; do
  if [ -f /tmp/anthares-android-done ]; then
    log "DONE_SIGNAL_RECEIVED"
    adb shell uiautomator dump /sdcard/kwai-ui.xml >/dev/null 2>&1 || true
    adb pull /sdcard/kwai-ui.xml /tmp/kwai-ui.xml >/dev/null 2>&1 || true
    if ! python3 kwai_auth_probe.py > /tmp/kwai-auth-probe.log 2>&1 || ! grep -qx "KWAI_AUTH_STATE=AUTHENTICATED_UI" /tmp/kwai-auth-probe.log; then
      log "LOGIN_NOT_CONFIRMED_IDENTITY_UNKNOWN"; rm -f /tmp/anthares-android-done
    else
      log "KWAI_LOGIN_CONFIRMED"
      capture
      # Do not persist a full AVD. Probe whether app-scoped state is exportable;
      # if not, the next stage will use a rootable disposable image and encrypted app-data only.
      adb shell run-as com.kwai.video id >>"$REPORT" 2>&1 && log "APP_STATE_RUN_AS_AVAILABLE" || log "APP_STATE_RUN_AS_UNAVAILABLE"
      bash kwai_session_state.sh save >>"$REPORT" 2>&1 || log "KWAI_SESSION_SAVE_WARNING"
      exit 0
    fi
  fi
  kill -0 "$UI_PID" 2>/dev/null || { log "FAIL: remote-ui-died-during-login"; exit 26; }
  kill -0 "$TUNNEL_PID" 2>/dev/null || { log "FAIL: tunnel-died-during-login"; exit 27; }
  sleep 1
done
log "FAIL: login-window-expired-120s"; exit 28

