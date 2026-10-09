#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# The upstream devcontainer image can contain an unrelated Yarn APT source
# with an expired/missing signing key. We do not install Yarn; disable only
# that source rather than weakening apt signature verification globally.
for source in /etc/apt/sources.list.d/*; do
  if [[ -f "$source" ]] && grep -q 'dl.yarnpkg.com/debian' "$source"; then
    sudo mv -- "$source" "${source}.disabled"
    echo "KWAI_CODESPACE_UNUSED_YARN_SOURCE_DISABLED=true"
  fi
done

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
