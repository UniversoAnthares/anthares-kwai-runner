#!/usr/bin/env bash
set -euo pipefail
# Run only on a dedicated Linux VM with Docker Engine + Compose installed.
# Registration credentials are never printed or committed to source control.
cd "$(dirname "$0")"
test "$(uname -s)" = "Linux" || { echo "REQUIRES_DEDICATED_LINUX=1" >&2; exit 2; }
test "$(id -u)" = "0" || { echo "RUN_AS_ROOT_ON_DEDICATED_VM=1" >&2; exit 2; }
command -v python3 >/dev/null
docker compose version >/dev/null
test -n "${CODEBERG_ADMIN_TOKEN:-}" || { echo "CODEBERG_ADMIN_TOKEN_REQUIRED=1" >&2; exit 2; }
install -d -m 0700 data
python3 - <<'PY'
import json,os,pathlib,urllib.request,urllib.error
url="https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner/actions/runners"
name="anthares-codeberg-linux-01"
hdr={"Authorization":"token "+os.environ["CODEBERG_ADMIN_TOKEN"],
     "Accept":"application/json","Content-Type":"application/json"}
config=pathlib.Path("data/runner-config.yml")
if config.exists():
    raise SystemExit("ALREADY_CONFIGURED_DO_NOT_REREGISTER")
def fetch(req):
    try:
        with urllib.request.urlopen(req,timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise SystemExit("CODEBERG_RUNNER_API_HTTP_"+str(exc.code)) from None
existing=fetch(urllib.request.Request(url+"?visible=false",headers=hdr))
if any(x.get("name")==name for x in existing):
    raise SystemExit("RUNNER_ALREADY_REGISTERED_RESTORE_CREDENTIALS_INSTEAD_OF_DUPLICATING")
body=json.dumps({"name":name,"ephemeral":False}).encode()
runner=fetch(urllib.request.Request(url,headers=hdr,data=body,method="POST"))
if not runner.get("uuid") or not runner.get("token") or not runner.get("id"):
    raise SystemExit("RUNNER_REGISTRATION_RESPONSE_INVALID")
config_text="""log:
  level: info
  job_level: info
runner:
  capacity: 1
  labels:
    - anthares-codeberg-linux:docker://ghcr.io/catthehacker/ubuntu:act-22.04
container:
  docker_host: tcp://engine:2375
  privileged: false
server:
  connections:
    anthares-repo:
      url: https://codeberg.org/
      uuid: %s
      token: %s
""" % (runner["uuid"],runner["token"])
fd=os.open(config,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
try:
    os.write(fd,config_text.encode())
finally:
    os.close(fd)
os.chown(config,1001,1001)
print("CODEBERG_REPO_SCOPED_RUNNER_REGISTERED_ID="+str(runner["id"]))
print("CODEBERG_RUNNER_TOKEN_LOGGED=0")
PY
unset CODEBERG_ADMIN_TOKEN
chown -R 1001:1001 data
docker compose -f compose.yml pull runner
docker compose -f compose.yml up -d
docker compose -f compose.yml ps
echo "CODEBERG_RUNNER_STARTED=1"
echo "Next: trigger .forgejo/workflows/codeberg-independent-runner-smoke.yml"
