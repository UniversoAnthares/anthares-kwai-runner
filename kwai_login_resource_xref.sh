#!/usr/bin/env bash
set -Eeuo pipefail
base="$(find kwai-vault -type f \( -name 'com.kwai.video.apk' -o -name 'base.apk' \) | head -1)"
[ -n "$base" ] || { echo BASE_NOT_FOUND; exit 2; }
echo "=== RESOURCE REFERENCES ==="
for term in tiny_login_content_container tiny_google_login_platform_item auth_token_login_button tiny_login_label tiny_login_close ll_profile; do
  echo "--- $term ---"
  strings "$base" | grep -i -B8 -A12 "$term" | head -n 120 || true
done
echo "=== MANIFEST CANDIDATES ==="
aapt dump xmltree "$base" AndroidManifest.xml 2>/dev/null | grep -Ei -B12 -A18 'login|auth|passport|account|profile|usercenter|user_center' | head -n 1800 || true
echo "=== DEX CLASS CANDIDATES ==="
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
unzip -q "$base" 'classes*.dex' -d "$tmp" || true
for dex in "$tmp"/classes*.dex; do
 [ -f "$dex" ] || continue
 strings "$dex" | grep -Ei '(^|[/.$])(login|auth|passport|account|profile|usercenter|user_center)[A-Za-z0-9_/$.-]*' | sort -u | head -n 700 || true
done
