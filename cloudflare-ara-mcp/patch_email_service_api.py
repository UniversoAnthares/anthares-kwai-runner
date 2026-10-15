#!/usr/bin/env python3
from pathlib import Path

p=Path(__file__).with_name('src')/'index.js'
s=p.read_text(encoding='utf-8')
s=s.replace("import { EmailMessage } from 'cloudflare:email';\n",'')
old="async function sendAuthEmail(env,code){if(!env.AUTH_EMAIL_SEND)throw new Error('email_binding_not_configured');const from=String(env.AUTH_EMAIL_FROM||'');if(!from||/[\\r\\n]/.test(from))throw new Error('email_sender_not_configured');const raw='From: Anthares Remote <'+from+'>\\r\\nTo: '+AUTH_EMAIL+'\\r\\nSubject: Codigo de autorizacao Anthares Remote\\r\\nMIME-Version: 1.0\\r\\nContent-Type: text/plain; charset=UTF-8\\r\\n\\r\\nSeu codigo de autorizacao e: '+code+'\\r\\nValidade: 10 minutos. Nao compartilhe este codigo.\\r\\n';await env.AUTH_EMAIL_SEND.send(new EmailMessage(from,AUTH_EMAIL,new ReadableStream({start(c){c.enqueue(te.encode(raw));c.close();}})));}"
new="async function sendAuthEmail(env,code){if(!env.AUTH_EMAIL_SEND)throw new Error('email_binding_not_configured');const from=String(env.AUTH_EMAIL_FROM||'');if(!from||/[\\r\\n]/.test(from))throw new Error('email_sender_not_configured');const text='Seu codigo de autorizacao Anthares Remote e: '+code+'\\nValidade: 10 minutos. Nao compartilhe este codigo.\\n';const r=await env.AUTH_EMAIL_SEND.send({to:AUTH_EMAIL,from,subject:'Codigo de autorizacao Anthares Remote',text});if(r&&r.messageId)console.log('oauth_email_sent message_id='+String(r.messageId).slice(0,80));}"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('sendAuthEmail target missing')
oldcatch="try{await sendAuthEmail(env,code);}catch(e){return json({error:'email_delivery_unavailable'},503);}"
newcatch="try{await sendAuthEmail(env,code);}catch(e){console.error('oauth_email_delivery_error '+String(e?.message||e).slice(0,180));return json({error:'email_delivery_unavailable'},503);}"
if oldcatch in s:
    s=s.replace(oldcatch,newcatch,1)
elif newcatch not in s:
    raise SystemExit('email catch target missing')
for forbidden in ("EmailMessage","new ReadableStream"):
    if forbidden in s: raise SystemExit('legacy email API remains: '+forbidden)
if "AUTH_EMAIL_SEND.send({to:AUTH_EMAIL,from" not in s: raise SystemExit('new email API missing')
p.write_text(s,encoding='utf-8')
print('ARA_EMAIL_SERVICE_API_PATCH_OK=1')
