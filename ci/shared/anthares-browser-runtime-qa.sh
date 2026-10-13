#!/usr/bin/env bash
set -Eeuo pipefail

PROVIDER="${CI_PROVIDER:-external}"
LANE="$(printf '%s' "$PROVIDER" | tr -cs 'A-Za-z0-9_.-' '-')"
CASES="${ANTHARES_BROWSER_QA_CASES:-40}"
IMAGE="anthares-browser:qa-${LANE}"

command -v docker >/dev/null
docker info >/dev/null

echo "ANTHARES_BROWSER_QA_PROVIDER=${PROVIDER}"
echo "ANTHARES_BROWSER_QA_CASES=${CASES}"
docker build -q -t "$IMAGE" anthares-brouser >/dev/null
docker pull -q nginx:alpine >/dev/null

CURRENT_NAME=""
CURRENT_PAGE=""
CURRENT_NET=""
CURRENT_VOL=""
CURRENT_TMP=""

cleanup_current() {
  [ -n "${CURRENT_NAME:-}" ] && docker rm -f "$CURRENT_NAME" >/dev/null 2>&1 || true
  [ -n "${CURRENT_PAGE:-}" ] && docker rm -f "$CURRENT_PAGE" >/dev/null 2>&1 || true
  [ -n "${CURRENT_NET:-}" ] && docker network rm "$CURRENT_NET" >/dev/null 2>&1 || true
  [ -n "${CURRENT_VOL:-}" ] && docker volume rm "$CURRENT_VOL" >/dev/null 2>&1 || true
  [ -n "${CURRENT_TMP:-}" ] && rm -rf "$CURRENT_TMP" || true
}
trap cleanup_current EXIT

wait_http() {
  local name="$1" url="$2"
  for _ in $(seq 1 90); do
    if curl -fsS "$url" >/dev/null 2>&1; then return 0; fi
    if ! docker ps --format '{{.Names}}' | grep -qx "$name"; then
      docker logs "$name" || true
      return 1
    fi
    sleep 0.5
  done
  docker logs "$name" || true
  return 1
}

for C in $(seq 1 "$CASES"); do
  GROUP=$(( (C-1) / 10 ))
  VARIANT=$(( (C-1) % 10 ))
  NAME="anthares-browser-${LANE}-${C}"
  PAGE_NAME="qa-page-${LANE}-${C}"
  VOL="anthares-browser-data-${LANE}-${C}"
  NET="anthares-browser-net-${LANE}-${C}"
  API_PORT=$((18080 + C))
  VNC_PORT=$((16080 + C))
  TOKEN="ci-control-${LANE}-${C}-g${GROUP}"
  PASS="ci-vnc-${LANE}-${C}-v${VARIANT}"
  PERSIST_SECRET="persist-${LANE}-${C}-${GROUP}-${VARIANT}"
  INPUT_TEXT="typed-${LANE}-${C}-${VARIANT}"
  CLICK_TEXT="clicked-${LANE}-${C}-${GROUP}"
  TMP_PAGE="$(mktemp -d)"

  CURRENT_NAME="$NAME"
  CURRENT_PAGE="$PAGE_NAME"
  CURRENT_NET="$NET"
  CURRENT_VOL="$VOL"
  CURRENT_TMP="$TMP_PAGE"

  cat >"$TMP_PAGE/index.html" <<HTML
<!doctype html>
<html><head><title>Anthares QA ${C}</title></head>
<body>
  <input id="qa-input" value="">
  <button id="qa-button" onclick="document.getElementById('qa-result').textContent='${CLICK_TEXT}'">click</button>
  <div id="qa-result">idle</div>
</body></html>
HTML

  docker volume create "$VOL" >/dev/null
  docker network create "$NET" >/dev/null
  docker run -d --name "$PAGE_NAME" --network "$NET" nginx:alpine >/dev/null
  docker cp "$TMP_PAGE/index.html" "$PAGE_NAME:/usr/share/nginx/html/index.html"

  start_container() {
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    docker run -d --name "$NAME" --network "$NET" \
      -p "${API_PORT}:8080" -p "${VNC_PORT}:6080" \
      -e "VNC_PASSWORD=${PASS}" \
      -e "CONTROL_TOKEN=${TOKEN}" \
      -e "START_URL=http://${PAGE_NAME}/" \
      -v "${VOL}:/data" \
      "$IMAGE" >/dev/null
  }

  auth_get() {
    curl -fsS -H "Authorization: Bearer ${TOKEN}" "http://127.0.0.1:${API_PORT}$1"
  }
  auth_post() {
    local path="$1" body="$2"
    curl -fsS -X POST -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
      -d "$body" "http://127.0.0.1:${API_PORT}${path}"
  }

  start_container
  wait_http "$NAME" "http://127.0.0.1:${API_PORT}/health"

  HEALTH=$(curl -fsS "http://127.0.0.1:${API_PORT}/health")
  python3 - "$HEALTH" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d.get('ok') is True, d
assert d.get('profile_dir_exists') is True, d
assert d.get('chromium_running') is True, d
assert d.get('cdp_ready') is True, d
PY

  for PATH_ in /status /page /targets /screenshot; do
    CODE=$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${API_PORT}${PATH_}")
    test "$CODE" = 401
    CODE=$(curl -sS -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer definitely-wrong' "http://127.0.0.1:${API_PORT}${PATH_}")
    test "$CODE" = 401
  done

  STATUS=$(auth_get /status)
  python3 - "$STATUS" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d.get('profile_dir_exists') is True, d
assert d.get('chromium_pids'), d
assert d.get('cdp_ready') is True, d
assert d.get('cdp_bind') == '127.0.0.1', d
assert d.get('session_claim') == 'not_verified', d
PY

  ! docker port "$NAME" | grep -q '9222'

  PAGE=$(auth_get /page)
  python3 - "$PAGE" "$C" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert f'Anthares QA {sys.argv[2]}' == d.get('title'), d
assert d.get('url','').startswith('http://qa-page-'), d
PY

  NAV=$(auth_post /navigate "{\"url\":\"http://${PAGE_NAME}/?via=navigate-${C}\",\"wait_ms\":300}")
  python3 - "$NAV" "$C" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert f'via=navigate-{sys.argv[2]}' in d.get('url',''), d
PY

  auth_post /wait '{"selector":"#qa-input","timeout_ms":5000,"visible":true}' >/dev/null
  TYPE=$(auth_post /type "{\"selector\":\"#qa-input\",\"text\":\"${INPUT_TEXT}\",\"clear\":true,\"wait_ms\":50}")
  python3 - "$TYPE" "$INPUT_TEXT" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d.get('ok') is True, d
assert d.get('chars') == len(sys.argv[2]), d
PY

  VALUE=$(auth_post /evaluate '{"expression":"document.querySelector(\"#qa-input\").value","return_by_value":true}')
  python3 - "$VALUE" "$INPUT_TEXT" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d['result'].get('value') == sys.argv[2], d
PY

  auth_post /click '{"selector":"#qa-button","wait_ms":50}' >/dev/null
  CLICKED=$(auth_post /evaluate '{"expression":"document.querySelector(\"#qa-result\").textContent","return_by_value":true}')
  python3 - "$CLICKED" "$CLICK_TEXT" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d['result'].get('value') == sys.argv[2], d
PY

  SHOT=$(auth_get /screenshot)
  python3 - "$SHOT" <<'PY'
import base64,json,sys
d=json.loads(sys.argv[1])
raw=base64.b64decode(d['base64'], validate=True)
assert d.get('format') == 'png', d
assert raw.startswith(b'\x89PNG\r\n\x1a\n'), raw[:16]
assert len(raw) > 1000, len(raw)
PY

  SETPERSIST=$(auth_post /evaluate "{\"expression\":\"localStorage.setItem('anthares_persist_secret','${PERSIST_SECRET}'); localStorage.getItem('anthares_persist_secret')\",\"return_by_value\":true}")
  python3 - "$SETPERSIST" "$PERSIST_SECRET" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d['result'].get('value') == sys.argv[2], d
PY

  docker rm -f "$NAME" >/dev/null
  start_container
  wait_http "$NAME" "http://127.0.0.1:${API_PORT}/health"
  auth_post /wait '{"selector":"body","timeout_ms":5000,"visible":true}' >/dev/null
  AFTER=$(auth_post /evaluate '{"expression":"localStorage.getItem(\"anthares_persist_secret\")","return_by_value":true}')
  python3 - "$AFTER" "$PERSIST_SECRET" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d['result'].get('value') == sys.argv[2], d
PY

  wait_http "$NAME" "http://127.0.0.1:${VNC_PORT}/vnc.html"
  curl -fsS "http://127.0.0.1:${VNC_PORT}/vnc.html" | grep -qi 'noVNC'

  echo "PROVIDER=${PROVIDER} CASE=${C} GROUP=${GROUP} VARIANT=${VARIANT} PASS"
  cleanup_current
  CURRENT_NAME=""
  CURRENT_PAGE=""
  CURRENT_NET=""
  CURRENT_VOL=""
  CURRENT_TMP=""
done

echo "PROVIDER=${PROVIDER} ALL_${CASES}_CASES=PASS"
echo 'CONTROL_API_AUTH=PASS CDP_LOOPBACK_ONLY=PASS'
echo 'NAVIGATE=PASS CLICK=PASS TYPE=PASS WAIT=PASS EVALUATE=PASS SCREENSHOT=PASS'
echo 'NOVNC_ENDPOINT=PASS CHROMIUM_RUNNING=PASS PERSISTENT_BROWSER_PROFILE_RESTART=PASS'
echo 'KWAI_AUTHENTICATED=NOT_TESTED PUBLISHED=NOT_TESTED'
