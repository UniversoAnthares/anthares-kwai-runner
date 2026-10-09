#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# All installation occurs inside the GitHub Codespace, never on the user's PC.
sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends \
  chromium xvfb openbox x11vnc novnc websockify \
  fonts-liberation ca-certificates >/dev/null

PRIVATE_HOME="${HOME}/.kwai-remote-private"
install -d -m 700 "${PRIVATE_HOME}" "${PRIVATE_HOME}/logs" "${PRIVATE_HOME}/chrome-profile"
python3 -m venv "${PRIVATE_HOME}/venv"
"${PRIVATE_HOME}/venv/bin/python" -m pip install --quiet --disable-pip-version-check 'playwright>=1.55,<2'
test -f /usr/share/novnc/vnc.html
command -v chromium >/dev/null
echo "KWAI_CODESPACE_INSTALL_OK=true"
echo "KWAI_CODESPACE_PRIVATE_PORTS=6080,8765"
echo "KWAI_CODESPACE_BROWSER_PROFILE=private_untracked_directory"
