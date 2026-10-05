#!/usr/bin/env bash
set -eu
mode="${1:?mode}"
base="$(find kwai-vault -type f \( -name 'com.kwai.video.apk' -o -name 'base.apk' \) | head -1)"
[ -n "$base" ] || { echo BASE_NOT_FOUND; exit 2; }
case "$mode" in
 activities) aapt dump xmltree "$base" AndroidManifest.xml 2>/dev/null | grep -Ei -B2 -A4 'activity|login|profile|account|passport|user' | head -n 500 || true;;
 services) aapt dump xmltree "$base" AndroidManifest.xml 2>/dev/null | grep -Ei -B2 -A4 'service|login|profile|account|passport|user' | head -n 500 || true;;
 receivers) aapt dump xmltree "$base" AndroidManifest.xml 2>/dev/null | grep -Ei -B2 -A4 'receiver|login|profile|account|passport|user' | head -n 500 || true;;
 providers) aapt dump xmltree "$base" AndroidManifest.xml 2>/dev/null | grep -Ei -B2 -A4 'provider|login|profile|account|passport|user' | head -n 500 || true;;
 schemes) aapt dump xmltree "$base" AndroidManifest.xml 2>/dev/null | grep -Ei -B3 -A6 'scheme|host|path|login|profile|account' | head -n 700 || true;;
 login-strings) strings "$base" | grep -Ei 'login|log_in|signin|sign_in|passport|account' | sort -u | head -n 500 || true;;
 profile-strings) strings "$base" | grep -Ei 'profile|user.?center|personal.?center|my.?profile|homepage' | sort -u | head -n 500 || true;;
 dfm-files) find kwai-vault -maxdepth 2 -type f -printf '%f\n' | sort; unzip -l "$base" | grep -Ei 'split|feature|dfm|profile|login|account' | head -n 700 || true;;
esac
echo "COMPONENT_PROBE_DONE=$mode"
