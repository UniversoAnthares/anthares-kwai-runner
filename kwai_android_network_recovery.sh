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

google_duplicate_account_visible(){
  dump_ui || return 1
  grep -Eqi 'account already exists on your device|already exists on this device|conta já existe neste dispositivo|conta ja existe neste dispositivo' /tmp/kwai-network-ui.xml
}

offline_visible(){
  dump_ui || return 1
  grep -Eqi 'Please check your Internet connection|check your Internet connection|No Internet connection|No network connection|Sem conexão|Sem internet|Verifique sua conexão|Verifique a sua conexão|Download failed\. Try again|Falha no download' /tmp/kwai-network-ui.xml
}

create_surface_visible(){
  dump_ui || return 1
  grep -Eqi 'record|camera|upload|post|create|album|gallery|photo|video|gravar|câmera|carregar|publicar|criar|álbum|galeria|foto|vídeo' /tmp/kwai-network-ui.xml &&
    ! grep -Eqi 'Continue with Google|Continuar com Google|Log in|Sign in|Entrar|Login' /tmp/kwai-network-ui.xml
}

bypass_offline_to_create(){
  local dims w h
  dims="$(adb shell wm size 2>/dev/null | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
  w="${dims%x*}"; h="${dims#*x}"
  [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]] || return 1

  log "KWAI_FALSE_OFFLINE_BYPASS_BEGIN"
  # First leave the broken Profile surface through Kwai's own Home tab.
  adb shell input tap $((w*10/100)) $((h*95/100)) >/dev/null 2>&1 || true
  sleep 3
  # Then invoke the central create route, which is independent of Profile.
  adb shell input tap $((w*50/100)) $((h*95/100)) >/dev/null 2>&1 || true
  sleep 4
  if create_surface_visible; then
    log "KWAI_FALSE_OFFLINE_BYPASS_CREATE_READY"
    : > /tmp/kwai-operational-bypass
    : > /tmp/anthares-android-done
    return 0
  fi

  # Some builds swallow the first Home/Plus pair while the offline overlay is
  # still attached. Try one clean navigation cycle without restarting the app.
  adb shell input tap $((w*10/100)) $((h*95/100)) >/dev/null 2>&1 || true
  sleep 2
  adb shell input tap $((w*50/100)) $((h*95/100)) >/dev/null 2>&1 || true
  sleep 4
  if create_surface_visible; then
    log "KWAI_FALSE_OFFLINE_BYPASS_CREATE_READY_SECOND_ATTEMPT"
    : > /tmp/kwai-operational-bypass
    : > /tmp/anthares-android-done
    return 0
  fi
  log "KWAI_FALSE_OFFLINE_BYPASS_NOT_READY"
  return 1
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
    local dims width height
    dims="$(adb shell wm size 2>/dev/null | tr -d '\r' | tail -1)"
    width="$(printf '%s' "$dims" | sed -nE 's/.* ([0-9]+)x([0-9]+).*/\1/p')"
    height="$(printf '%s' "$dims" | sed -nE 's/.* ([0-9]+)x([0-9]+).*/\2/p')"
    if [[ "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ ]]; then
      xy="$((width/2)) $((height*46/100))"
    else
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
  if printf '%s\n' "$d" | grep -E 'Transports: WIFI.*VALIDATED|VALIDATED.*Transports: WIFI' >/dev/null; then
    log "ANDROID_WIFI_VALIDATED=1"
  else
    log "ANDROID_WIFI_VALIDATED=0"
  fi
  if adb shell ip route 2>/dev/null | grep -q '^default\| default '; then
    log "ANDROID_DEFAULT_ROUTE=1"
  else
    log "ANDROID_DEFAULT_ROUTE=0"
  fi
}

capture_kwai_hosts(){
  local tmp=/tmp/kwai-hosts.txt
  adb logcat -d -t 3000 2>/dev/null | grep -Eio '([a-z0-9-]+\.)+(kwai\.com|kwai\.net|kwai-pro\.com|kuaishou\.com)' | tr 'A-Z' 'a-z' | sort -u | tail -40 > "$tmp" || true
  if [ -s "$tmp" ]; then
    log "KWAI_HOST_PROBE_BEGIN"
    while read -r host; do
      [ -n "$host" ] || continue
      if adb shell ping -c 1 -W 2 "$host" >/dev/null 2>&1; then
        log "KWAI_HOST_DNS_OK=$host"
      else
        log "KWAI_HOST_DNS_OR_ICMP_FAIL=$host"
      fi
    done < "$tmp"
    log "KWAI_HOST_PROBE_END"
  fi
}

normalize_network(){
  log "ANDROID_NETWORK_RECOVERY_BEGIN"
  adb shell cmd connectivity airplane-mode disable >/dev/null 2>&1 || true
  adb shell settings put global airplane_mode_on 0 >/dev/null 2>&1 || true
  adb shell svc wifi enable >/dev/null 2>&1 || true
  adb shell svc data disable >/dev/null 2>&1 || true
  adb shell settings put global mobile_data 0 >/dev/null 2>&1 || true
  adb shell cmd netpolicy set restrict-background false >/dev/null 2>&1 || true
  log "ANDROID_NETWORK_MODE=WIFI_ONLY"

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
    if adb shell dumpsys connectivity 2>/dev/null | grep -E 'Transports: WIFI.*VALIDATED|VALIDATED.*Transports: WIFI' >/dev/null; then
      log "ANDROID_WIFI_VALIDATED_ATTEMPT=$i"
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
    if adb shell dumpsys connectivity 2>/dev/null | grep -E 'Transports: WIFI.*VALIDATED|VALIDATED.*Transports: WIFI' >/dev/null; then
      log "ANDROID_NETWORK_PREFLIGHT_WIFI_VALIDATED_ATTEMPT=$i"
      return 0
    fi
    sleep 2
  done
  log "ANDROID_NETWORK_PREFLIGHT_WIFI_VALIDATION_PENDING"
  return 0
}

watch(){
  : >> "$LOG"
  local total=0 last_snapshot=0 last_bypass=0
  log "KWAI_OFFLINE_DIAGNOSTIC_WATCH_STARTED"
  while true; do
    if google_sso_foreground; then
      if google_duplicate_account_visible; then
        log "GOOGLE_DUPLICATE_ACCOUNT_SCREEN_DETECTED"
        adb shell input keyevent KEYCODE_BACK >/dev/null 2>&1 || true
        sleep 2
        log "GOOGLE_DUPLICATE_ACCOUNT_SCREEN_DISMISSED"
      else
        sleep 4
      fi
      continue
    fi
    if kwai_foreground && offline_visible; then
      total=$((total+1))
      log "KWAI_OFFLINE_SCREEN_STILL_PRESENT count=$total"
      now="$(date +%s)"
      if [ $((now-last_bypass)) -ge 20 ]; then
        last_bypass="$now"
        bypass_offline_to_create || true
      fi
      if [ $((now-last_snapshot)) -ge 25 ]; then
        connectivity_snapshot
        adb logcat -d -t 2000 2>/dev/null | grep -Ei 'UnknownHost|SSLHandshake|CertPath|ConnectException|SocketTimeout|ERR_|Cronet|hodor|kwai|download failed|resource|HTTP.?40[13]|HTTP.?50[0-9]|auth.*fail|login.*fail|OnFailed|error_code' | tail -160 >> "$LOG" || true
        adb shell dumpsys package com.kwai.video 2>/dev/null | grep -E 'versionName=|versionCode=|primaryCpuAbi=|secondaryCpuAbi=|android.permission.INTERNET' | head -20 >> "$LOG" || true
        capture_kwai_hosts
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
    capture_kwai_hosts
    if offline_visible; then
      log "KWAI_OFFLINE_SCREEN_PRESENT_MANUAL_RETRY_INEFFECTIVE"
      bypass_offline_to_create || true
    fi
    ;;
  *) echo "usage: $0 {preflight|watch|once}" >&2; exit 2 ;;
esac
