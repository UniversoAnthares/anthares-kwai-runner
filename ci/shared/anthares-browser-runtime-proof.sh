#!/usr/bin/env bash
set -Eeuo pipefail

TMP="$(mktemp)"
cp ci/shared/anthares-browser-runtime-qa.sh "$TMP"
python3 - "$TMP" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
old='  docker rm -f "$NAME" >/dev/null\n  start_container\n'
new='  docker stop -t 10 "$NAME" >/dev/null\n  docker rm "$NAME" >/dev/null 2>&1 || true\n  sleep 0.5\n  start_container\n'
if old not in s:
    raise SystemExit('QA_GRACEFUL_RESTART_PATCH_TARGET_MISSING')
p.write_text(s.replace(old,new,1))
PY
chmod +x "$TMP"
ANTHARES_BROWSER_QA_CASES="${ANTHARES_BROWSER_QA_CASES:-3}" bash "$TMP"
rm -f "$TMP"
