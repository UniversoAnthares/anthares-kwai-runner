import crypto from 'node:crypto';

// The Codeberg identity is cryptographically independent of GitHub OIDC.
// Producer authority is restricted to the exact clipper workflow on main.
const ISSUER='https://codeberg.org/api/actions';
const KEYS_URL='https://codeberg.org/api/actions/.well-known/keys';
const REPOSITORY='UniversoAnthares/anthares-kwai-runner';
const PRODUCER_REPOSITORY='UniversoAnthares/anthares-clipper';
const PRODUCER_WORKFLOW='cortes-tiktok-neon-producer.yml';
let jwks=null,validUntil=0;

export async function codebergRole(req,audience,workflowName) {
  const m=/^Bearer\s+(.+)$/i.exec(String(req.headers?.authorization||''));
  const jwt=m?m[1]:'';
  if(jwt.length<200||jwt.length>16000)return '';
  const parts=jwt.split('.');
  if(parts.length!==3)return '';
  let hdr,claims;
  try{
    hdr=JSON.parse(Buffer.from(parts[0],'base64url').toString('utf8'));
    claims=JSON.parse(Buffer.from(parts[1],'base64url').toString('utf8'));
  }catch{return '';}
  if(hdr.alg!=='RS256'||!/^[A-Za-z0-9_.-]{1,200}$/.test(hdr.kid||''))return '';
  const now=Math.floor(Date.now()/1000);
  const aud=Array.isArray(claims.aud)?claims.aud:[claims.aud];
  const producer=claims.repository===PRODUCER_REPOSITORY;
  const expectedRepo=producer?PRODUCER_REPOSITORY:REPOSITORY;
  const expectedWorkflow=producer?PRODUCER_WORKFLOW:workflowName;
  const wf=expectedRepo+'/.forgejo/workflows/'+expectedWorkflow+'@refs/heads/main';
  const allowedEvents=producer?['workflow_dispatch','push','schedule']:['schedule','workflow_dispatch'];
  if(claims.iss!==ISSUER||!aud.includes(audience)||
     claims.repository!==expectedRepo||claims.ref!=='refs/heads/main'||
     claims.workflow_ref!==wf||!allowedEvents.includes(claims.event_name))return '';
  if(!Number.isFinite(claims.exp)||claims.exp<=now||claims.exp>now+3600||
     !Number.isFinite(claims.iat)||claims.iat>now+60||
     (claims.nbf!==undefined&&Number(claims.nbf)>now+60))return '';
  try{
    if(!jwks||Date.now()>validUntil){
      const rsp=await fetch(KEYS_URL,{signal:AbortSignal.timeout(7500)});
      if(!rsp.ok)return '';
      const data=await rsp.json();
      if(!Array.isArray(data.keys))return '';
      jwks=data;validUntil=Date.now()+300000;
    }
    const k=jwks.keys.find(k=>k.kid===hdr.kid&&k.kty==='RSA'&&(!k.alg||k.alg==='RS256'));
    if(!k)return '';
    const publicKey=crypto.createPublicKey({key:k,format:'jwk'});
    return crypto.verify('RSA-SHA256',Buffer.from(parts[0]+'.'+parts[1]),
      publicKey,Buffer.from(parts[2],'base64url'))?(producer?'producer':'consumer'):'';
  }catch{return '';}
}

export async function codebergConsumerRole(req,audience,workflowName){
 const role=await codebergRole(req,audience,workflowName);
 return role==='consumer'?role:'';
}
