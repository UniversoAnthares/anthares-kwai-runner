#!/usr/bin/env bash
set -u
PHASE="${1:-snapshot}"
OUT="${KWAI_NETWORK_DIAGNOSTICS_FILE:-kwai-network-diagnostics.txt}"
redact(){ sed -E 's/([?&](token|access_token|auth|password|cookie|session|sid)=)[^&[:space:]]+/\1<redacted>/Ig'; }
{
  echo "===== KWAI_ANDROID_NETWORK phase=${PHASE} utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  echo "## adb"
  timeout 8 adb devices -l 2>&1 || true
  echo "## clock"
  timeout 8 adb shell 'date -u; date; getprop persist.sys.timezone' 2>&1 || true
  echo "## android connectivity"
  timeout 12 adb shell dumpsys connectivity 2>&1 | grep -E 'DefaultNetwork|NetworkAgentInfo|NetworkCapabilities|NET_CAPABILITY_(INTERNET|VALIDATED)|VALIDATED|INTERNET|TRANSPORT_' | head -120 || true
  echo "## routes"
  timeout 8 adb shell 'ip route; ip -6 route' 2>&1 || true
  echo "## dns properties"
  timeout 8 adb shell getprop 2>&1 | grep -Ei '\[.*dns.*\]|net\.dns' | head -80 || true
  echo "private_dns_mode=$(timeout 5 adb shell settings get global private_dns_mode 2>/dev/null | tr -d '\r')"
  echo "private_dns_specifier=$(timeout 5 adb shell settings get global private_dns_specifier 2>/dev/null | tr -d '\r')"
  echo "## dns/ip probes from Android"
  timeout 10 adb shell 'ping -c 2 -W 3 1.1.1.1' 2>&1 || true
  timeout 10 adb shell 'ping -c 2 -W 3 google.com' 2>&1 || true
  timeout 10 adb shell 'ping -c 2 -W 3 connectivitycheck.gstatic.com' 2>&1 || true
  echo "## Android-side HTTPS capability"
  timeout 20 adb shell 'if command -v curl >/dev/null 2>&1; then curl -fsSIL --max-time 12 https://connectivitycheck.gstatic.com/generate_204 | head -12; elif command -v wget >/dev/null 2>&1; then wget -S -O /dev/null -T 12 https://connectivitycheck.gstatic.com/generate_204; elif toybox --list 2>/dev/null | grep -qx wget; then toybox wget -S -O /dev/null https://connectivitycheck.gstatic.com/generate_204; else echo ANDROID_HTTPS_CLIENT_UNAVAILABLE_USE_NET_CAPABILITY_VALIDATED; fi' 2>&1 || echo ANDROID_HTTPS_PROBE_TIMEOUT_OR_FAILURE
  echo "## Kwai package network permission"
  timeout 10 adb shell dumpsys package com.kwai.video 2>&1 | grep -E 'userId=|android.permission.INTERNET|android.permission.ACCESS_NETWORK_STATE' | head -30 || true
  echo "## filtered network/tls errors"
  if [ -s /tmp/kwai-login-logcat.txt ]; then
    grep -Ei -B4 -A12 'UnknownHostException|SSLHandshakeException|SSLException|CertificateException|CertPath|ConnectException|SocketTimeoutException|ECONN|ENETUNREACH|EHOSTUNREACH|Cronet|OkHttp|NetworkSecurityConfig|dns[^ ]* (fail|error)|network[^ ]* (fail|error)|handshake[^ ]* (fail|error)' /tmp/kwai-login-logcat.txt | tail -320 | redact || true
    echo "## Kwai process network/error context"
    kwai_pid="$(timeout 5 adb shell pidof com.kwai.video 2>/dev/null | tr -d '\r' | awk '{print $1}')"
    echo "KWAI_PID=${kwai_pid:-none}"
    if [ -n "${kwai_pid:-}" ]; then
      grep -E "[[:space:]]${kwai_pid}[[:space:]]" /tmp/kwai-login-logcat.txt | grep -Ei 'System\.err|Aegon|retrofit|Cronet|OkHttp|network|dns|ssl|tls|http|Exception|error|fail|timeout|response' | tail -360 | redact || true
    fi
  else
    timeout 10 adb shell logcat -d -t 1800 2>&1 | grep -Ei -B4 -A12 'UnknownHostException|SSLHandshakeException|SSLException|CertificateException|CertPath|ConnectException|SocketTimeoutException|ECONN|ENETUNREACH|EHOSTUNREACH|Cronet|OkHttp|NetworkSecurityConfig|dns[^ ]* (fail|error)|network[^ ]* (fail|error)|handshake[^ ]* (fail|error)' | tail -320 | redact || true
  fi
  echo "===== END_KWAI_ANDROID_NETWORK phase=${PHASE} ====="
} >> "$OUT"
