#!/usr/bin/env bash
set -Eeuo pipefail
base="$(find kwai-vault -type f \( -name 'com.kwai.video.apk' -o -name 'base.apk' \) -print -quit)"
if [ -z "$base" ] || [ ! -f "$base" ]; then echo "TEST_VALIDITY=BASE_NOT_FOUND"; exit 90; fi
sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
aapt_bin="$(find "$sdk/build-tools" -type f -name aapt -perm -111 2>/dev/null | sort -V | tail -1)"
if [ -z "$aapt_bin" ] || [ ! -x "$aapt_bin" ]; then echo "TEST_VALIDITY=AAPT_NOT_FOUND"; exit 91; fi
echo "AAPT_PATH=$aapt_bin"
"$aapt_bin" version
"$aapt_bin" dump xmltree "$base" AndroidManifest.xml > manifest-tree.txt
if [ ! -s manifest-tree.txt ]; then echo "TEST_VALIDITY=EMPTY_MANIFEST"; exit 92; fi
echo "TEST_VALIDITY=OK"
grep -Ei -B14 -A28 'TinyLoginActivity|TinyUserInfoActivity|TinyGoogleSSOActivity|AutoLoginActivity|AutoLogoutActivity|KwaiAuthActivity|LivePartnerAuthActivity|login|auth|user.?info|profile' manifest-tree.txt > login-activity-metadata.txt || true
cat login-activity-metadata.txt
if grep -Eqi 'TinyLoginActivity|TinyUserInfoActivity|TinyGoogleSSOActivity|AutoLoginActivity|AutoLogoutActivity|KwaiAuthActivity|LivePartnerAuthActivity' login-activity-metadata.txt; then
 echo "SUCCESS_SIGNAL=KNOWN_LOGIN_COMPONENT_DECLARED"; exit 0
fi
if grep -Eqi 'login|auth|user.?info|profile' login-activity-metadata.txt; then
 echo "SUCCESS_SIGNAL=AUTH_RELATED_COMPONENT_DECLARED"; exit 0
fi
echo "FAILURE_SIGNAL=NO_AUTH_COMPONENT_DECLARED"; exit 20
