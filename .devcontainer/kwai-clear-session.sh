#!/usr/bin/env bash
set -euo pipefail

# Run INSIDE the GitHub Codespace to terminate remote Chrome and erase its
# local unencrypted browser profile. This does not affect GitHub Actions caches.
PRIVATE_HOME="${HOME}/.kwai-remote-private"
PROFILE="${PRIVATE_HOME}/chrome-profile"
for name in inspector chrome novnc vnc openbox xvfb; do
  pidfile="${PRIVATE_HOME}/${name}.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if [[ "$pid" =~ ^[0-9]+$ ]]; then
      kill "$pid" 2>/dev/null || true
    fi
    rm -f -- "$pidfile"
  fi
done
sleep 2
if [[ "$PROFILE" != "${HOME}/.kwai-remote-private/chrome-profile" ]]; then
  echo "Refusing unsafe profile deletion" >&2
  exit 1
fi
if [[ -d "$PROFILE" ]]; then
  find "$PROFILE" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
fi
echo "KWAI_CODESPACE_CHROME_PROFILE_ERASED=true"
echo "To reopen Chrome, run: bash .devcontainer/kwai-start.sh"
