#!/usr/bin/env bash
set -Eeuo pipefail
base="$(find kwai-vault -type f \( -name 'com.kwai.video.apk' -o -name 'base.apk' \) -print -quit)"
sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"; aapt_bin="$(find "$sdk/build-tools" -type f -name aapt -perm -111 2>/dev/null | sort -V | tail -1)"
[ -f "$base" ] && [ -x "$aapt_bin" ] || { echo TEST_VALIDITY=INVALID; exit 90; }
"$aapt_bin" dump xmltree "$base" AndroidManifest.xml > manifest-tree.txt
python3 - <<'PY'
import re
s=open("manifest-tree.txt",errors="ignore").read().splitlines()
targets=("com.yxcorp.gifshow.oauth.activity.OpenAuthActivity","com.yxcorp.gifshow.auth.LivePartnerAuthActivity","com.yxcorp.gifshow.authorization.KwaiAuthActivity","com.yxcorp.gifshow.tiny.login.activity.TinyUserInfoActivity")
for i,line in enumerate(s):
 if any(t in line for t in targets):
  lo=max(0,i-3); hi=min(len(s),i+42)
  print("TARGET_BLOCK_BEGIN");print("\n".join(s[lo:hi]));print("TARGET_BLOCK_END")
print("TEST_VALIDITY=OK")
PY
