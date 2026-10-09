#!/usr/bin/env bash
set -Eeuo pipefail
report=kwai-album-smoke-status.txt
: > "$report"
record(){ printf '%s\n' "$1" | tee -a "$report"; }
record 'MODE=READ_ONLY_NO_LOGIN_NO_POST'
bash kwai_vault_install.sh >/dev/null
record 'KWAI_APP_INSTALLED=1'
ffmpeg -hide_banner -loglevel error -f lavfi -i 'color=c=black:s=320x568:r=15:d=2' -f lavfi -i 'anullsrc=r=44100:cl=mono' -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -y /tmp/kwai-album-test.mp4
adb push /tmp/kwai-album-test.mp4 /sdcard/Movies/kwai-album-test.mp4 >/dev/null
adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Movies/kwai-album-test.mp4 >/dev/null
record 'ANDROID_MEDIA_PUSHED=1'
if adb shell pm path com.kwai.video | grep -q package:; then record 'KWAI_PACKAGE_VISIBLE=1'; else record 'KWAI_PACKAGE_VISIBLE=0'; exit 41; fi
if adb shell ls /sdcard/Movies/kwai-album-test.mp4 | grep -q kwai-album-test.mp4; then record 'ANDROID_ALBUM_FILE_PRESENT=1'; else record 'ANDROID_ALBUM_FILE_PRESENT=0'; exit 42; fi
record 'UPLOAD_NOT_TESTED=1'
record 'PUBLICATION_NOT_TESTED=1'
