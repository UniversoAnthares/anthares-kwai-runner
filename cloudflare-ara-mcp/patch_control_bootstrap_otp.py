#!/usr/bin/env python3
from pathlib import Path
import re

p=Path(__file__).with_name('src')/'index.js'
s=p.read_text(encoding='utf-8')

helper_anchor="async function status(env,device=DEFAULT_DEVICE){return controlJson(env,`/v1/mcp/status?device_id=${encodeURIComponent(device)}`);}"
helper=helper_anchor+"\nasync function bootstrapOtpStatus(env){try{const r=await controlJson(env,'/v1/mcp/oauth/bootstrap-status');console.log('oauth_bootstrap_status active='+String(!!r.active));return r;}catch(e){console.error('oauth_bootstrap_status_error '+String(e?.message||e).slice(0,180));return{active:false};}}\nasync function verifyBootstrapOtp(env,code){try{const r=await controlJson(env,'/v1/mcp/oauth/bootstrap-verify',{method:'POST',body:{code:String(code||'')}});return!!r.ok;}catch(e){console.error('oauth_bootstrap_verify_error '+String(e?.message||e).slice(0,180));return false;}}"
if 'async function bootstrapOtpStatus(' not in s:
    if helper_anchor not in s: raise SystemExit('status helper anchor missing')
    s=s.replace(helper_anchor,helper,1)

old="async verifyEmailChallenge(txId,code){return eq(await this.createEmailChallenge(txId),String(code||''));}"
new="async verifyEmailChallenge(txId,code){const v=String(code||'');if(await verifyBootstrapOtp(this.env,v))return true;return eq(await this.createEmailChallenge(txId),v);}"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('verifyEmailChallenge target missing')

pattern=re.compile(r"const code=await st\(env\)\.createEmailChallenge\(tx\);if\(!code\)return json\(\{error:'rate_limited'\},429\);try\{await sendAuthEmail\(env,code\);\}catch\(e\)\{[^}]*return json\(\{error:'email_delivery_unavailable'\},503\);\}")
replacement="const bs=await bootstrapOtpStatus(env);if(!bs.active){const code=await st(env).createEmailChallenge(tx);if(!code)return json({error:'rate_limited'},429);try{await sendAuthEmail(env,code);}catch(e){console.error('oauth_email_delivery_error '+String(e?.message||e).slice(0,180));return json({error:'email_delivery_unavailable'},503);}}"
s,n=pattern.subn(replacement,s,count=1)
if n!=1 and 'const bs=await bootstrapOtpStatus(env);if(!bs.active)' not in s:
    raise SystemExit('authorize bootstrap control replacement failed')

s=s.replace('Digite o código de configuração enviado ao e-mail cadastrado.','Digite o código temporário enviado ao e-mail cadastrado.')

for required in ['bootstrapOtpStatus','verifyBootstrapOtp','bootstrap-status','bootstrap-verify','oauth_bootstrap_status_error']:
    if required not in s: raise SystemExit('missing '+required)

p.write_text(s,encoding='utf-8')
print('ARA_CONTROL_BOOTSTRAP_OTP_PATCH_OK=1')
