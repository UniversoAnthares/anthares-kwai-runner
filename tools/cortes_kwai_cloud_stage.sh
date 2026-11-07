#!/usr/bin/env bash
set -Eeuo pipefail
# Canonical Neon is the sole queue authority on the hosted Android.
export KWAI_EXPECTED_ACCOUNT=lucasrosalem
python3 tools/cortes_kwai_neon_cloud.py status > /tmp/kwai-neon-status.txt
if ! grep -Eq '^KWAI_NEON_ELIGIBLE=[1-9][0-9]*$' /tmp/kwai-neon-status.txt; then
  echo KWAI_NEON_NO_ELIGIBLE_SAFE_CUT=1
  exit 0
fi
test -n "${KWAI_SESSION_ENCRYPTION_KEY:-}" && test -s kwai-session.enc || {
  echo KWAI_AUTH_SESSION_REQUIRED; exit 66;
}
bash kwai_vault_install.sh
bash kwai_session_state.sh restore
python3 kwai_auth_probe.py > /tmp/kwai-identity.txt
grep -qx 'KWAI_AUTH_STATE=AUTHENTICATED_UI' /tmp/kwai-identity.txt
grep -qx 'KWAI_IDENTITY_PROFILE_MATCH=1' /tmp/kwai-identity.txt
python3 tools/cortes_kwai_neon_cloud.py lease --json '{"lease_seconds":600}' > /tmp/kwai-lease.txt
if grep -qx 'KWAI_NEON_LEASE=NONE' /tmp/kwai-lease.txt; then
  echo KWAI_NEON_EMPTY_AFTER_CAS=1
  exit 0
fi
grep -qx 'KWAI_NEON_LEASE=ACQUIRED' /tmp/kwai-lease.txt
release_fenced(){
  trap - ERR
  python3 - <<'PY'
import json
d=json.load(open('kwai-neon-lease.json',encoding='utf-8'))
with open('/tmp/kwai-release.json','w',encoding='utf-8') as f:
 json.dump({'id':d['id'],'lease_generation':int(d['lease_generation'])},f)
PY
  python3 tools/cortes_kwai_neon_cloud.py fail --json @/tmp/kwai-release.json
}
trap release_fenced ERR
eval "$(python3 - <<'PY'
import json,shlex,re
from urllib.parse import urlsplit
d=json.load(open('kwai-neon-lease.json',encoding='utf-8'))
p=d.get('payload') or {}
id=str(d['id'])
assert re.fullmatch(r'kwai-cortes-[A-Za-z0-9._:-]{3,145}',id)
assert d['target_key']=='kwai:lucasrosalem' and int(d['lease_generation'])>=1
assert p.get('expected_account')=='lucasrosalem'
source=str(p['source_id'])
start=str(p['source_start']);end=str(p['source_end'])
url=str(p['video_url']);u=urlsplit(url)
assert source in id and id.endswith('-'+start+'-'+end)
assert u.scheme=='https' and u.hostname in ('anthares.us','www.anthares.us')
assert u.path.endswith('_'+start+'_'+end+'.mp4')
title=str(p.get('video_title') or p.get('title') or '')
assert title and len(title)<=180
data={'KWAI_QUEUE_JOB_ID':id,'KWAI_LEASE_GENERATION':str(d['lease_generation']),
      'KWAI_SOURCE_ID':source,'KWAI_SOURCE_START':start,'KWAI_SOURCE_END':end,
      'KWAI_VIDEO_URL':url,'KWAI_VIDEO_TITLE':title}
digest=str(p.get('content_sha256') or p.get('media_content_sha256') or '').lower()
if digest:
 assert re.fullmatch(r'[0-9a-f]{64}',digest)
 data['KWAI_EXPECTED_MEDIA_SHA256']=digest
for k,v in data.items():
 assert '\r' not in v and '\n' not in v and '\x00' not in v
 print('export '+k+'='+shlex.quote(v))
PY
)"
if [ "${KWAI_CLOUD_MODE:-stage}" = publish ]; then
  test "${KWAI_CLOUD_PUBLISH_ENABLED:-0}" = 1 || {
    echo KWAI_NEON_PUBLICATION_DISABLED; exit 65;
  }
  test "${KWAI_INDEPENDENT_VERIFIER_ENABLED:-0}" = 1 || {
    echo KWAI_NEON_INDEPENDENT_VERIFIER_REQUIRED; exit 65;
  }
  export KWAI_QUEUE_BACKEND=neon
  export KWAI_LEASE_RENEW_INTERVAL_SECONDS=120 KWAI_LEASE_RENEW_TTL_SECONDS=600
  bash kwai_publish.sh
  trap - ERR
  echo KWAI_NEON_CANONICAL_PUBLICATION_COMPLETE=1
  exit 0
fi
# KW-05 stages and verifies media, then releases this unstarted lease. KW-06
# controls the irreversible publication path above.
python3 tools/kwai_media_stage.py
eval "$(python3 - <<'PY'
import json,shlex
d=json.load(open('kwai-media-ready.json',encoding='utf-8'))
for src,dst in [('sha256','KWAI_MEDIA_SHA256'),('size','KWAI_MEDIA_SIZE'),
                ('name','KWAI_MEDIA_NAME'),('remote_path','KWAI_ANDROID_VIDEO'),
                ('media_uri','KWAI_ANDROID_MEDIA_URI')]:
 print('export '+dst+'='+shlex.quote(str(d[src])))
PY
)"
python3 kwai_publish_video.py prepare > /tmp/kwai-prepared.txt
grep -qx 'STATE=READY_TO_PUBLISH' /tmp/kwai-prepared.txt
echo KWAI_NEON_MEDIA_PREPARED=1
release_fenced
echo KWAI_KW05_PREPARE_FENCED=PASS
