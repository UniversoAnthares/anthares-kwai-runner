#!/usr/bin/env bash
set -euo pipefail
base="$HOME/.anthares-forgejo"
bin="$base/bin"; data="$base/data"; conf="$base/custom/conf"
mkdir -p "$bin" "$data" "$conf"
chmod 700 "$base"
fj="$bin/forgejo"
cf="$bin/cloudflared"
if [ ! -x "$fj" ]; then
  curl -fsSL -o "$fj" https://code.forgejo.org/forgejo/forgejo/releases/download/v15.0.9/forgejo-15.0.9-linux-amd64
  chmod 700 "$fj"
fi
if [ ! -x "$cf" ]; then
  curl -fsSL -o "$cf" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod 700 "$cf"
fi
cat > "$conf/app.ini" <<EOF
APP_NAME = Anthares Forgejo Redundancy
RUN_USER = $(id -un)
RUN_MODE = prod
[server]
PROTOCOL = http
HTTP_ADDR = 127.0.0.1
HTTP_PORT = 3001
ROOT_URL = http://127.0.0.1:3001/
OFFLINE_MODE = true
DISABLE_SSH = true
[database]
DB_TYPE = sqlite3
PATH = $data/forgejo.db
[repository]
ROOT = $data/repositories
[security]
INSTALL_LOCK = true
[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW = false
EOF
pkill -f "$fj web" 2>/dev/null || true
nohup "$fj" web --config "$conf/app.ini" >"$base/forgejo.log" 2>&1 &
for i in $(seq 1 30); do curl -fsS http://127.0.0.1:3001/api/v1/version >/dev/null && break; sleep 1; done
curl -fsS http://127.0.0.1:3001/api/v1/version
if ! "$fj" admin user list --config "$conf/app.ini" 2>/dev/null | grep -q '^1[[:space:]]'; then
  pw="$(openssl rand -base64 36 | tr -d '\n')"
  printf '%s' "$pw" > "$base/admin.password"; chmod 600 "$base/admin.password"
  "$fj" admin user create --config "$conf/app.ini" --username anthares-admin --password "$pw" --email anthares-forgejo@localhost.invalid --admin --must-change-password=false >/dev/null
fi
if [ ! -s "$base/api.token" ]; then
  "$fj" admin user generate-access-token --config "$conf/app.ini" --username anthares-admin --token-name anthares-agents --scopes all > "$base/token.out"
  sed -n 's/.*Access token was successfully created: //p' "$base/token.out" > "$base/api.token"
  rm -f "$base/token.out"; chmod 600 "$base/api.token"
fi
token="$(cat "$base/api.token")"
if ! curl -fsS -H "Authorization: token $token" http://127.0.0.1:3001/api/v1/repos/anthares-admin/anthares-kwai-runner >/dev/null 2>&1; then
  curl -fsS -X POST -H "Authorization: token $token" -H 'Content-Type: application/json'     -d '{"name":"anthares-kwai-runner","private":false,"description":"Anthares GitHub-independent Forgejo redundancy"}'     http://127.0.0.1:3001/api/v1/user/repos >/dev/null
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
git clone --mirror https://github.com/UniversoAnthares/anthares-kwai-runner.git "$tmp/repo.git" >/dev/null 2>&1
cd "$tmp/repo.git"
git push --mirror "http://anthares-admin:$token@127.0.0.1:3001/anthares-admin/anthares-kwai-runner.git" >/dev/null 2>&1
src="$(git rev-parse refs/heads/main)"
dst="$(git ls-remote "http://anthares-admin:$token@127.0.0.1:3001/anthares-admin/anthares-kwai-runner.git" refs/heads/main | awk '{print $1}')"
[ "$src" = "$dst" ]
pkill -f "$cf tunnel --url http://127.0.0.1:3001" 2>/dev/null || true
nohup "$cf" tunnel --no-autoupdate --url http://127.0.0.1:3001 >"$base/cloudflared.log" 2>&1 &
for i in $(seq 1 30); do
  url="$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' "$base/cloudflared.log" | tail -1 || true)"
  [ -n "$url" ] && break
  sleep 1
done
printf '%s' "$url" > "$base/public.url"; chmod 600 "$base/public.url"
echo "FORGEJO_LOCAL=PROVEN"
echo "MIRROR_SHA=$dst"
echo "PUBLIC_URL=$url"
