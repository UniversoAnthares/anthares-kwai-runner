#!/usr/bin/env bash
set -u

MODE="${1:-preflight}"
LOG="${KWAI_NETWORK_RECOVERY_LOG:-/tmp/kwai-network-recovery.log}"

log(){ printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

dump_ui(){
  adb shell uiautomator dump /sdcard/kwai-network-ui.xml >/dev/null 2>&1 || return 1
  adb pull /sdcard/kwai-network-ui.xml /tmp/kwai-network-ui.xml >/dev/null 2>&1 || return 1
  [ -s /tmp/kwai-network-ui.xml ]
}

focus_text(){
  adb shell dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | tail -2 | tr '\n' ' '
}

google_sso_foreground(){ focus_text | grep -Eq 'com\.google\.android\.gms|GoogleSSOActivity|SignInHubActivity|SignInActivity'; }
kwai_foreground(){ focus_text | grep -q 'com\.kwai\.video'; }

offline_visible(){
  dump_ui || return 1
  grep -Eqi 'Please check your Internet connection|check your Internet connection|No Internet connection|No network connection|Sem conexão|Sem internet|Verifique sua conexão|Verifique a sua conexão|Download failed\. Try again|Falha no download' /tmp/kwai-network-ui.xml
}

tap_retry(){
  dump_ui || return 1
  local xy
  xy="$(python3 - <<'PY'
import re, xml.etree.ElementTree as ET
try:
    root = ET.parse('/tmp/kwai-network-ui.xml').getroot()
except Exception:
    raise SystemExit(1)
pat = re.compile(r'^(retry|try again|tentar novamente|tente novamente|repetir)$', re.I)
for n in root.iter('node'):
    label = ((n.get('text') or '') + ' ' + (n.get('content-desc') or '')).strip()
    if not pat.search(label):
        continue
    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', n.get('bounds',''))
    if m:
        a,b,c,d = map(int,m.groups())
        print((a+c)//2, (b+d)//2)
        break
PY
)"
  if [ -z "$xy" ]; then
    # The Kwai offline screen sometimes renders Retry without accessibility labels.
    # Fallback uses the stable central button location, scaled to the display.
    local dims width height
    dims="$(adb shell wm size 2>/dev/null | tr -d '\r' | tail -1)"
    width="$(printf '%s' "$dims" | sed -nE 's/.* ([0-9]+)x([0-9]+).*/\1/p')"
    height="$(printf '%s' "$dims" | sed -nE 's/.* ([0-9]+)x([0-9]+).*/\2/p')"
    if [[ "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ ]]; then
      xy="$((width/2)) $((height*55/100))"
      log "KWAI_OFFLINE_RETRY_COORDINATE_FALLBACK"
    else
      log "KWAI_OFFLINE_RETRY_NO_COORDINATES"
      return 1
    fi
  fi
  adb shell input tap $xy >/dev/null 2>&1 || return 1
  log "KWAI_OFFLINE_RETRY_TAPPED"
}

connectivity_snapshot(){
  local d
  d="$(adb shell dumpsys connectivity 2>/dev/null || true)"
  if printf '%s\n' "$d" | grep -q 'VALIDATED'; then
    log "ANDROID_NETWORK_VALIDATED=1"
  else
    log "ANDROID_NETWORK_VALIDATED=0"
  fi
  if adb shell ip route 2>/dev/null | grep -q '^default\| default '; then
    log "ANDROID_DEFAULT_ROUTE=1"
  else
    log "ANDROID_DEFAULT_ROUTE=0"
  fi
}

normalize_network(){
  log "ANDROID_NETWORK_RECOVERY_BEGIN"
  adb shell cmd connectivity airplane-mode disable >/dev/null 2>&1 || true
  adb shell settings put global airplane_mode_on 0 >/dev/null 2>&1 || true
  adb shell svc wifi enable >/dev/null 2>&1 || true

  private_mode="$(adb shell settings get global private_dns_mode 2>/dev/null | tr -d '\r' || true)"
  private_spec="$(adb shell settings get global private_dns_specifier 2>/dev/null | tr -d '\r' || true)"
  proxy="$(adb shell settings get global http_proxy 2>/dev/null | tr -d '\r' || true)"
  log "ANDROID_PRIVATE_DNS_MODE=${private_mode:-unknown}"
  [ -z "$private_spec" ] || [ "$private_spec" = "null" ] || log "ANDROID_PRIVATE_DNS_SPECIFIER_PRESENT=1"
  log "ANDROID_HTTP_PROXY=${proxy:-unknown}"
  if [ "$private_mode" = "hostname" ] || { [ -n "$private_spec" ] && [ "$private_spec" != "null" ]; }; then
    adb shell settings put global private_dns_mode opportunistic >/dev/null 2>&1 || true
    adb shell settings delete global private_dns_specifier >/dev/null 2>&1 || true
    log "ANDROID_PRIVATE_DNS_RESET=1"
  fi
  if [ -n "$proxy" ] && [ "$proxy" != "null" ] && [ "$proxy" != ":0" ]; then
    adb shell settings put global http_proxy :0 >/dev/null 2>&1 || true
    log "ANDROID_HTTP_PROXY_RESET=1"
  fi

  for i in $(seq 1 12); do
    if adb shell ip route 2>/dev/null | grep -q '^default\| default '; then
      log "ANDROID_NETWORK_ROUTE_READY_ATTEMPT=$i"
      break
    fi
    sleep 2
  done
  connectivity_snapshot
  log "ANDROID_NETWORK_RECOVERY_END"
}

preflight(){
  : > "$LOG"
  normalize_network
  for i in $(seq 1 15); do
    if adb shell dumpsys connectivity 2>/dev/null | grep -q 'VALIDATED'; then
      log "ANDROID_NETWORK_PREFLIGHT_VALIDATED_ATTEMPT=$i"
      return 0
    fi
    sleep 2
  done
  log "ANDROID_NETWORK_PREFLIGHT_VALIDATION_PENDING"
  return 0
}

watch(){
  : >> "$LOG"
  local total=0 last_snapshot=0
  log "KWAI_OFFLINE_DIAGNOSTIC_WATCH_STARTED"
  while true; do
    if google_sso_foreground; then
      sleep 4
      continue
    fi
    if kwai_foreground && offline_visible; then
      total=$((total+1))
      log "KWAI_OFFLINE_SCREEN_STILL_PRESENT count=$total"
      now="$(date +%s)"
      if [ $((now-last_snapshot)) -ge 25 ]; then
        connectivity_snapshot
        adb logcat -d -t 1500 2>/dev/null | grep -Ei 'UnknownHost|SSLHandshake|CertPath|ConnectException|SocketTimeout|ERR_|Cronet|hodor|kwai|download failed|resource' | tail -90 >> "$LOG" || true
        adb shell dumpsys package com.kwai.video 2>/dev/null | grep -E 'versionName=|versionCode=|primaryCpuAbi=|android.permission.INTERNET' | head -15 >> "$LOG" || true
        last_snapshot="$now"
      fi
    fi
    sleep 5
  done
}

case "$MODE" in
  preflight) preflight ;;
  watch) watch ;;
  once)
    connectivity_snapshot
    if offline_visible; then log "KWAI_OFFLINE_SCREEN_PRESENT_MANUAL_RETRY_INEFFECTIVE"; fi
    ;;
  *) echo "usage: $0 {preflight|watch|once}" >&2; exit 2 ;;
esac
