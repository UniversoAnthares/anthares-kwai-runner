import crypto from 'node:crypto';
const ISS='https://anthares.us/forgejo/api/actions',AUD='urn:anthares:forgejo:identity-proof:v1',REPO='anthares-admin/anthares-ci-sandbox',WF=REPO+'/.forgejo/workflows/forgejo-identity-proof.yml@refs/heads/main';
const reply=(r,s,x)=>{r.statusCode=s;r.setHeader('Content-Type','application/json');r.setHeader('Cache-Control','no-store');r.end(JSON.stringify(x));};
export default async function handler(req,res){
 if(req.method!=='GET')return reply(res,405,{ok:false});
 const m=/^Bearer\s+([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/i.exec(String(req.headers.authorization||'')),jwt=m?.[1]||'';
 if(jwt.length<200||jwt.length>16000)return reply(res,401,{ok:false});
 try{
 const p=jwt.split('.'),h=JSON.parse(Buffer.from(p[0],'base64url').toString()),c=JSON.parse(Buffer.from(p[1],'base64url').toString()),now=Math.floor(Date.now()/1000),aud=Array.isArray(c.aud)?c.aud:[c.aud];
 if(h.alg!=='RS256'||!/^[A-Za-z0-9_.-]{1,200}$/.test(h.kid||'')||c.iss!==ISS||!aud.includes(AUD)||c.repository!==REPO||c.repository_owner!=='anthares-admin'||c.sub!=='repo:'+REPO+':ref:refs/heads/main'||c.ref!=='refs/heads/main'||c.workflow_ref!==WF||c.event_name!=='workflow_dispatch'||!Number.isInteger(c.iat)||!Number.isInteger(c.exp)||c.iat>now+60||c.exp<=now||c.exp>now+3600||c.exp-c.iat>3600||(c.nbf!==undefined&&Number(c.nbf)>now+60))return reply(res,401,{ok:false});
 const r=await fetch(ISS+'/.well-known/keys',{signal:AbortSignal.timeout(8000)});
 if(!r.ok)return reply(r¶»§q«^