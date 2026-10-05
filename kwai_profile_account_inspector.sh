#!/usr/bin/env bash
set -Eeuo pipefail
bash kwai_vault_install.sh
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 8
python3 kwai_profile_account_inspector.py
