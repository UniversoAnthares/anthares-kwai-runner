#!/usr/bin/env bash
set -Eeuo pipefail
# Hosted Android: single canonical Neon ledger; no Cloudflare/PC queue fallback.
export KWAI_EXPECTED_ACCOUNT=lucasrosalem
test "${KWAI_CLOUD_PUBLISH_ENABLED:-0}" = 1 || { echo KWAI_KW05_GATE_DISABLED; exit 65; }
test "${KWAI_INDEPENDENT_VERIFIER_ENABLED:-0}" = 1 || { echo KWAI_VERIFIER_GATE_DISABLED; exit 65; }
test -n "${KWAI_SESSION_ENCRYPTION_KEY:-}" && test -s kwai-session.enc || { echo KWAI_AUTH_SESSION_REQUIRED; exit 66; }
bash kwai_vault_install.sh
bash kwai_session_state.sh restore
python3 kwai_auth_probe.py >/tmp/kwai-identity.txt
grep -qx KWAI_AUTH_STATE=AUTHENTICATED_UI /tmp/kwai-identity.txt
grep -qx KWAI_IDENTITY_PROFILE_MATCH=1 /tmp/kwai-identity.txt
python3 tools/cortes_kwai_neon_cloud.py status >/tmp/kwai-neon-hold.txt
grep -qx KWAI_NEON_UNCERTAIN=0 /tmp/kwai-neon-hold.txt || { echo KWAI_UNCERTAIN_HOLD=1; exit 67; }
python3 tools/cortes_kwai_neon_cloud.py lease --json '{"lease_seconds":600}' >/tmp/kwai-lease.txt
grep -qx KWAI_NEON_LEASE=ACQUIRED /tmp/kwai-lease.txt || { echo KWAI_QUEUE_EMPTY=1; exit 0; }
# A lease must be released if publication has not started.
release_prestart() {
  python3 -c 'import json; d=json.load(open("kwai-neon-lease.json")); json.dump({"id":d["id"],"lease_generation":int(d["lease_generation"])},open("/tmp/kwai-release.json","w"))'
  python3 tools/cortes_kwai_neon_cloud.py fail --json @/tmp/kwai-release.json
}
trap release_prestart ERR
eval "$(python3 - <<'PY'
import json,shlex,re
from urllib.parse import urlsplit
d=json.load(open('kwai-neon-lease.json'))
p=d.get('payload') or {}
job=str(d.get('id') or '')
assert re.fullmatch(r'kwai-cortes-[A-Za-z0-9._:-]{3,145}',job)
assert d['target_key']=='kwai:lucasrosalem' and int(d['lease_generation'])>=1
assert p['expected_account']=='lucasrosalem'
source=str(p['source_id']); start=str(p['source_start']); end=str(p['source_end'])
url=str(p['video_url']); u=urlsplit(url)
assert source in job and job.endswith('-'+start+'-'+end)
assert u.scheme=='https' and u.hostname in ('anthares.us','www.anthares.us')
assert u.path.endswith('_'+start+'_'+end+'.mp4')
title=str(p.get('video_title') or p.get('title') or '')
assert title and len(title)<=180
vals={'KWAI_QUEUE_JOB_ID':job,'KWAI_SOURCE_ID':source,'KWAI_SOURCE_START':start,
      'KWAI_SOURCE_END':end,'KWAI_VIDEO_URL':url,'KWAI_VIDEO_TITLE':title}
digest=str(p.get('content_sha256') or p.get('media_content_sha256') or '').lower()
if digest:
 assert re.fullmatch(r'[0-9a-f]{64}',digest)
 vals['KWAI_EXPECTED_MEDIA_SHA256']=digest
for k,v in vals.items():
 assert '\n' not in v and '\r' not in v
 print('export '+k+'='+shlex.quote(v))
PY
)"
python3 tools/kwai_media_stage.py
eval "$(python3 - <<'PY'
import json,shlex
d=json.load(open('kwai-media-ready.json'))
for key,name in [('sha256','KWAI_MEDIA_SHA256'),('size','KWAI_MEDIA_SIZE'),('name','KWAI_MEDIA_NAME'),('remote_path','KWAI_ANDROID_VIDEO'),('media_uri','KWAI_ANDROID_MEDIA_URI')]:
 print('export '+name+'='+shlex.quote(str(d[key])))
PY
)"
python3 kwai_publish_video.py prepare >/tmp/kwai-prepare.txt
grep -qx STATE=READY_TO_PUBLISH /tmp/kwai-prepare.txt
echo KWAI_NEON_MEDIA_PREPARED=1
# KW-05 stops before the irreversible click. KW-06 supplies real publication
# and an independent account readback signed by the verifier.
release_prestart
trap - ERR
echo KWAI_KW05_PREPARE_FENCED=PASS
