#!/usr/bin/env bash
set -Eeuo pipefail
case "${1:?case}" in
01) adb shell getprop ro.build.version.sdk ;;
02) adb shell getprop ro.product.cpu.abilist ;;
03) adb shell getprop ro.dalvik.vm.native.bridge ;;
04) adb shell wm density ;;
05) find kwai-vault -type f -name '*.apk' -printf '%f\n' | sort ;;
06) find kwai-vault -type f -name '*.apk' | wc -l ;;
07) find kwai-vault -type f -name 'base.apk' -o -name 'com.kwai.video.apk' ;;
08) find kwai-vault -type f -iname '*arm64*' -printf '%f\n' ;;
09) find kwai-vault -type f -iname '*x86_64*' -printf '%f\n' ;;
10) find kwai-vault -type f -iname '*mdpi*' -printf '%f\n' ;;
11) find kwai-vault -type f -iname '*hdpi*' -printf '%f\n' ;;
12) find kwai-vault -type f -iname '*xxhdpi*' -printf '%f\n' ;;
13) find kwai-vault -type f -iname '*language*' -o -iname '*lang*' ;;
14) find kwai-vault -type f -iname '*feature*' -printf '%f\n' ;;
15) find kwai-vault -type f -name '*.apk' -exec sha256sum {} \; ;;
16) for f in $(find kwai-vault -type f -name '*.apk'); do aapt dump badging "$f" 2>/dev/null | head -2 || true; done ;;
17) adb shell pm list packages -3 ;;
18) adb shell df -h /data ;;
19) adb shell getprop ro.build.version.release ;;
20) adb shell getprop ro.product.device ;;
*) exit 2 ;;
esac
echo "APK_DIAG_${1}=PASS"
