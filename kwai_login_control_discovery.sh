#!/usr/bin/env bash
set -Eeuo pipefail
bash kwai_vault_install.sh
adb shell pm grant com.kwai.video android.permission.POST_NOTIFICATIONS >/dev/null 2>&1 || true
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 8
python3 kwai_login_control_discovery.py
