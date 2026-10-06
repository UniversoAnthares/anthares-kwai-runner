#!/usr/bin/env bash
set -euo pipefail
base="$HOME/.anthares-forgejo"; bin="$base/bin"; data="$base/data"; conf="$base/custom/conf"
mkdir -p "$bin" "$data" "$conf"; chmod 700 "$base"
fj="$bin/forgejo"; cf="$bin/cloudflared"; sock="$base/forgejo.sock"
if [ ! -x "$fj" ]; then curl -fsSL -o "$fj" https://code.forgejo.org/forgejo/forgejo/releases/download/v15.0.9/forgejo-15.0.9-linux-amd64; chmod 700 "$fj"; fi
if [ ! -x "$cf" ]; then curl -fsSL -o "$cf" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod 700 "$cf"; fi
cat > "$conf/app.ini" <<EOF
APP_NAME = Anthares Forgejo Redundancy
RUN_USER = $(id -un)
RUN_MODE = prod
[server]
PROTOCOL = http+unix
HTTP_ADDR = $sock
UNIX_SOCKET_PERMISSION = 600
ROOT_URL = http://unix/
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
pkill -f "$fj web" 2>/dev/null || true; rm -f "$sock"
nohup "$fj" web --config "$conf/app.ini" >"$base/forgejo.log" 2>&1 &
for i in $(seq 1 40); do curl -fsS --unix-socket "$sock" http://unix/api/v1/version >/dev/null 2>&1 && break; sleep 1; done
curl -fsS --unix-socket "$sock" http://unix/api/v1/version
if ! "$fj" admin user list --config "$conf/app.ini" 2>/dev/null | grep -q 'anthares-admin'; then
  pw="$(openssl rand -base64 36 | tr -d '\n')"; printf '%s' "$pw" > "$base/admin.password"; chmod 600 "$base/admin.password"
  "$fj" admin user create --config "$conf/app.ini" --username anthares-admin --password "$pw" --email anthares-forgejo@localhost.invalid --admin --must-change-password=false >/dev/null
fi
if [ ! -s "$base/api.token" ]; then
  "$fj" admin user generate-access-token --config "$conf/app.ini" --username anthares-admin --token-name anthares-agents --scopes all > "$base/token.out"
  sed -n 's/.*Access token was successfully created: //p' "$base/token.out" > "$base/api.token"; rm -f "$base/token.out"; chmod 600 "$base/api.token"
fi
token="$(cat "$base/api.token")"
api(){ curl -fsS --unix-socket "$sock" -H "Authorization: token $token" "$@"; }
if ! api http://unix/api/v1/repos/anthares-admin/anthares-kwai-runner >/dev/null 2>&1; then
  api -X POST -H 'Content-Type: application/json' -d '{"clone_addr":"https://github.com/UniversoAnthares/anthares-kwai-runner.git","repo_name":"anthares-kwai-runner","mirror":true,"private":false,"service":"git"}' http://unix/api/v1/repos/migrate >/dev/null
fi
for i in $(seq 1 60); do dst="$(api http://unix/api/v1/repos/anthares-admin/anthares-kwai-runner/branches/main 2>/dev/null | sed -n 's/.*"id":"\([0-9a-f]\{40\}\)".*/\1/p' | head -1 || true)"; [ -n "$dst" ] && break; sleep 1; done
src="$(git ls-remote https://github.com/UniversoAnthares/anthares-kwai-runner.git refs/heads/main | awk '{print $1}')"
[ "$src" = "$dst" ] || { echo "SHA_MISMATCH source=$src target=$dst"; exit 2; }
pkill -f "$cf tunnel --url unix:$sock" 2>/dev/null || true
nohup "$cf" tunnel --no-autoupdate --url "unix:$sock" >"$base/cloudflared.log" 2>&1 &
url=""
for i in $(seq 1 40); do url="$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' "$base/cloudflared.log" | tail -1 || true)"; [ -n "$url" ] && break; sleep 1; done
[ -n "$url" ] || { echo "TUNNEL_URL_MISSING"; exit 3; }
printf '%s' "$url" > "$base/public.url"; chmod 600 "$base/public.url"
echo "FORGEJO_LOCAL=PROVEN"; echo "MIRROR_SHA=$dst"; echo "PUBLIC_URL=$url"
