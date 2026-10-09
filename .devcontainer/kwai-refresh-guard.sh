#!/usr/bin/env bash
set -euo pipefail

# Codespaces only. Restart the private identity inspector, not Chrome or VNC.
# Never erase the authenticated Chrome profile or copy its session anywhere.
cd "$(dirname "$0")/.."
pidfile="${HOME}/.kwai-remote-private/inspector.pid"
if [[ -f "$pidfile" ]]; then
  pid="$(cat "$pidfile")"
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    if [[ -r "/proc/${pid}/cmdline" ]] && tr '\0' ' ' <"/proc/${pid}/cmdline" | grep -Fq 'kwai-identity-guard.py'; then
      kill "$pid"
      for _ in 1 2 3 4 5 6 7 8 9 10; do
        kill -0 "$pid" 2>/dev/null || break
        [[ "$(ps -o stat= -p "$pid" 2>/dev/null)" != Z* ]] || break
        sleep 0.2
      done
      if kill -0 "$pid" 2>/dev/null && [[ "$(ps -o stat= -p "$pid" 2>/dev/null)" != Z* ]]; then
        echo "KWAI_GUARD_REFRESH=inspector_did_not_exit" >&2
        exit 1
      fi
    else
      echo "KWAI_GUARD_REFRESH=pid_mismatch_refusing_to_kill" >&2
      exit 1
    fi
  fi
  rm -f "$pidfile"
fi
bash .devcontainer/kwai-start.sh
python3 - <<'PY'
import json,time,urllib.request
for _ in range(30):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/health",timeout=2) as r:
            assert json.load(r)["ready"] is True
        print("KWAI_GUARD_REFRESH=ready;chrome_profile_untouched=true")
        break
    except Exception:
        time.sleep(0.25)
else:
    raise SystemExit("KWAI_GUARD_REFRESH=health_failed")
PY
