#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).with_name("src") / "index.js"
s = p.read_text(encoding="utf-8")

old_control = "const CONTROL='https://anthares-ara-backup.anthares1.workers.dev';"
new_control = "const CONTROL='https://anthares-ara-vercel-reserve.vercel.app';"
if old_control in s:
    s = s.replace(old_control, new_control, 1)
elif new_control not in s:
    raise SystemExit('CONTROL target not found')

helper_anchor = "async function controlJson(env,path,opts){const r=await control(env,path,opts);const raw=await r.text();let data={};try{data=raw?JSON.parse(raw):{};}catch{data={raw};}if(!r.ok)throw new Error(`control ${r.status}: ${data.error||data.raw||'request failed'}`);return data;}\n"
helper = "async function consumeViaControl(env,kind,jti,exp){try{await controlJson(env,'/v1/mcp/oauth/consume',{method:'POST',body:{kind,issuer:ORIGIN,jti,exp}});return true;}catch{return false;}}\n"
if 'async function consumeViaControl(' not in s:
    if helper_anchor not in s:
        raise SystemExit('controlJson anchor missing')
    s = s.replace(helper_anchor, helper_anchor + helper, 1)

old_auth = "!(await st(env).consume('authorization_code',p.jti,p.exp))"
new_auth = "!(await consumeViaControl(env,'authorization_code',p.jti,p.exp))"
if old_auth in s:
    s = s.replace(old_auth, new_auth, 1)
elif new_auth not in s:
    raise SystemExit('authorization-code consume target missing')

old_refresh = "!(await st(env).consume('refresh_token',p.jti,p.exp))"
new_refresh = "!(await consumeViaControl(env,'refresh_token',p.jti,p.exp))"
if old_refresh in s:
    s = s.replace(old_refresh, new_refresh, 1)
elif new_refresh not in s:
    raise SystemExit('refresh consume target missing')

required = [
    new_control,
    "async function consumeViaControl(",
    "consumeViaControl(env,'authorization_code'",
    "consumeViaControl(env,'refresh_token'",
]
for marker in required:
    if marker not in s:
        raise SystemExit('missing marker: ' + marker)

p.write_text(s, encoding='utf-8')
print('ARA_VERCEL_PRIMARY_PATCH_OK=1')
