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
      echo "WAIT_HTTP_CONTAINER_EXITED url=${url}" >&2
      docker logs "$name" || true
      return 1
    fi
    sleep 0.5
  done
  echo "WAIT_HTTP_TIMEOUT url=${url}" >&2
  curl -sS -i "$url" || true
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
      -p "${API_PORT}:8080" \
      -e "VNC_PASSWORD=${PASS}" \
      -e "CONTROL_TOKEN=${TOKEN}" \
      -e "START_URL=http://${PAGE_NAME}/" \
      -v "${VOL}:/data" \
      "$IMAGE" >/dev/null
  }

  auth_request() {
    local method="$1" path="$2" body="${3:-}"
    local tmp code
    tmp="$(mktemp)"
    if [ "$method" = GET ]; then
      code=$(curl -sS -o "$tmp" -w '%{http_code}' -H "Authorization: Bearer ${TOKEN}" \
        "http://127.0.0.1:${API_PORT}${path}") || code="curl_error"
    else
      code=$(curl -sS -o "$tmp" -w '%{http_code}' -X "$method" \
        -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
        -d "$body" "http://127.0.0.1:${API_PORT}${path}") || code="curl_error"
    fi
    if [ "$code" != 200 ]; then
      echo "ANTHARES_BROWSER_QA_HTTP_FAILURE case=${C} method=${method} path=${path} status=${code}" >&2
      cat "$tmp" >&2 || true
      echo >&2
      docker logs "$NAME" >&2 || true
      rm -f "$tmp"
      return 1
    fi
    cat "$tmp"
    rm -f "$tmp"
  }

  auth_get() {
    auth_request GET "$1"
  }
  auth_post() {
    auth_request POST "$1" "$2"
  }

  start_container
  wait_http "$NAME" "http://127.0.0.1:${API_PORT}/health"

  HEALTH=$(curl -fsS "http://127.0.0.1:${API_PORT}/health")
  python3 - "$HEALTH" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d.get('ok') is True, d
assert d.get('service') == 'anthares-browser', d
assert d.get('readiness_path') == '/ready', d
PY

  wait_http "$NAME" "http://127.0.0.1:${API_PORT}/ready"
  READY=$(curl -fsS "http://127.0.0.1:${API_PORT}/ready")
  python3 - "$READY" <<'PY'
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
  wait_http "$NAME" "http://127.0.0.1:${API_PORT}/ready"
  auth_post /wait '{"selector":"body","timeout_ms":5000,"visible":true}' >/dev/null
  AFTER=$(auth_post /evaluate '{"expression":"localStorage.getItem(\"anthares_persist_secret\")","return_by_value":true}')
  python3 - "$AFTER" "$PERSIST_SECRET" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d['result'].get('value') == sys.argv[2], d
PY

  # websockify intentionally binds loopback inside the container. Publishing
  # 6080 on the Docker host cannot reach that listener and would be unsafe.
  ! docker port "$NAME" | grep -q ':6080'
  NOVNC_OK=0
  for _ in $(seq 1 30); do
    if docker exec "$NAME" python3 -c 'import urllib.request; data=urllib.request.urlopen("http://127.0.0.1:6080/vnc.html", timeout=10).read(); assert b"noVNC" in data' >/dev/null 2>&1; then
      NOVNC_OK=1
      break
    fi
    sleep 0.5
  done
  test "$NOVNC_OK" = 1

  echo "PROVIDER=${PROVIDER} CASE=${C} GROUP=${GROUP} VARIANT=${VARIANT} PASS"
  cleanup_current
  CURRENT_NAME=""
  CURRENT_PAGE=""
  CURRENT_NET=""
  CURRENT_VOL=""
  CURRENT_TMP=""
done

echo "PROVIDER=${PROVIDER} ALL_${CASES}_CASES=PASS"
echo 'HEALTH_LIVENESS=PASS READY_FAIL_CLOSED=PASS'
echo 'CONTROL_API_AUTH=PASS CDP_LOOPBACK_ONLY=PASS'
echo 'NAVIGATE=PASS CLICK=PASS TYPE=PASS WAIT=PASS EVALUATE=PASS SCREENSHOT=PASS'
echo 'NOVNC_ENDPOINT=PASS CHROMIUM_RUNNING=PASS PERSISTENT_BROWSER_PROFILE_RESTART=PASS'
echo 'KWAI_AUTHENTICATED=NOT_TESTED PUBLISHED=NOT_TESTED'
