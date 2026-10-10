#!/usr/bin/env bash
set -euo pipefail

# All installation occurs inside the GitHub Codespace, never on the user's PC.
IS_ALPINE=false
if command -v apk >/dev/null 2>&1; then
  IS_ALPINE=true
  sudo apk add --no-cache \
    chromium xvfb openbox x11vnc novnc websockify \
    ttf-liberation ca-certificates python3 py3-pip py3-virtualenv >/dev/null
elif command -v apt-get >/dev/null 2>&1; then
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

  sudo apt-get update -qq
  sudo apt-get install -y -qq --no-install-recommends \
    chromium xvfb openbox x11vnc novnc websockify \
    fonts-liberation ca-certificates python3-venv python3-pip >/dev/null
else
  echo "KWAI_CODESPACE_UNSUPPORTED_PACKAGE_MANAGER=true" >&2
  exit 1
fi

PERSISTENT_ROOT="${ANTHARES_PERSISTENT_ROOT:-/workspaces/.anthares-private}"
PRIVATE_HOME="${KWAI_PRIVATE_HOME:-${PERSISTENT_ROOT}/kwai}"
LEGACY_PRIVATE_HOME="${HOME}/.kwai-remote-private"
install -d -m 700 "${PERSISTENT_ROOT}" "${PRIVATE_HOME}" "${LEGACY_PRIVATE_HOME}"

# One-time in-place migration from the earlier Codespaces-only location. The
# profile stays inside the same Codespace account and is never exported.
if [[ -d "${LEGACY_PRIVATE_HOME}/chrome-profile" && ! -e "${PRIVATE_HOME}/.legacy-profile-migrated" ]]; then
  if [[ ! -d "${PRIVATE_HOME}/chrome-profile/Default" ]]; then
    cp -a "${LEGACY_PRIVATE_HOME}/." "${PRIVATE_HOME}/"
    echo "KWAI_CODESPACE_LEGACY_PROFILE_MIGRATED=true"
  else
    echo "KWAI_CODESPACE_LEGACY_PROFILE_MIGRATED=skipped_existing_persistent_profile"
  fi
  : > "${PRIVATE_HOME}/.legacy-profile-migrated"
  chmod 600 "${PRIVATE_HOME}/.legacy-profile-migrated"
fi
install -d -m 700 "${PRIVATE_HOME}" "${PRIVATE_HOME}/logs" "${PRIVATE_HOME}/chrome-profile"
chmod 700 "${PERSISTENT_ROOT}" "${PRIVATE_HOME}" "${PRIVATE_HOME}/chrome-profile"

# Bridge v2 predates the workspace-backed profile and still reads its ledger
# from ~/.kwai-remote-private. Keep that path backward compatible while storing
# the ledger itself in /workspaces so a devcontainer rebuild cannot replay old
# authorized commands.
LEGACY_BRIDGE_STATE="${LEGACY_PRIVATE_HOME}/bridge-v2-seen.json"
PERSISTENT_BRIDGE_STATE="${PRIVATE_HOME}/bridge-v2-seen.json"
if [[ -f "${LEGACY_BRIDGE_STATE}" && ! -e "${PERSISTENT_BRIDGE_STATE}" && ! -L "${LEGACY_BRIDGE_STATE}" ]]; then
  cp -a "${LEGACY_BRIDGE_STATE}" "${PERSISTENT_BRIDGE_STATE}"
fi
if [[ -e "${LEGACY_BRIDGE_STATE}" || -L "${LEGACY_BRIDGE_STATE}" ]]; then
  rm -f -- "${LEGACY_BRIDGE_STATE}"
fi
ln -s "${PERSISTENT_BRIDGE_STATE}" "${LEGACY_BRIDGE_STATE}"

if [[ ! -x "${PRIVATE_HOME}/venv/bin/python" ]]; then
  if ! python3 -m venv "${PRIVATE_HOME}/venv" 2>/dev/null; then
    virtualenv "${PRIVATE_HOME}/venv"
  fi
fi

if [[ "$IS_ALPINE" == true ]]; then
  # Python Playwright does not publish musllinux wheels. Use the native
  # Chromium DevTools Protocol client dependencies instead.
  "${PRIVATE_HOME}/venv/bin/python" -m pip install --quiet --disable-pip-version-check \
    websocket-client requests
  echo "KWAI_CODESPACE_BROWSER_CONTROL=cdp"
else
  "${PRIVATE_HOME}/venv/bin/python" -m pip install --quiet --disable-pip-version-check \
    'playwright>=1.55,<2'
  echo "KWAI_CODESPACE_BROWSER_CONTROL=playwright"
fi

NOVNC_WEB=""
for candidate in /usr/share/novnc /usr/share/webapps/novnc; do
  if [[ -f "$candidate/vnc.html" ]]; then
    NOVNC_WEB="$candidate"
    break
  fi
done
[[ -n "$NOVNC_WEB" ]] || { echo "KWAI_CODESPACE_NOVNC_WEB_NOT_FOUND=true" >&2; exit 1; }
printf '%s\n' "$NOVNC_WEB" > "${PRIVATE_HOME}/novnc-web-root"
chmod 600 "${PRIVATE_HOME}/novnc-web-root"

command -v chromium >/dev/null
command -v Xvfb >/dev/null
command -v openbox-session >/dev/null
command -v x11vnc >/dev/null
command -v websockify >/dev/null

echo "KWAI_CODESPACE_INSTALL_OK=true"
echo "KWAI_CODESPACE_PRIVATE_PORTS=6080,8765"
echo "KWAI_CODESPACE_BROWSER_PROFILE=persistent_private_workspace_directory"
echo "KWAI_CODESPACE_PERSISTENT_ROOT=${PERSISTENT_ROOT}"
echo "KWAI_CODESPACE_BRIDGE_LEDGER=persistent_private_workspace_directory"
echo "KWAI_CODESPACE_NOVNC_WEB=$NOVNC_WEB"
