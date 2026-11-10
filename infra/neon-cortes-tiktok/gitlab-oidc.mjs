import crypto from 'node:crypto';

// Protected GitLab Clipper may enqueue existing shorts, never claim/publish them.
// Verify the complete signed token; job-level CI flags alone are untrusted.
const ISSUER='https://gitlab.com';
const PROJECT='UniversoAnthares/anthares-clipper';
const PROJECT_ID='87361774';
const SUBJECT='project_path:'+PROJECT+':ref_type:branch:ref:main';
let cachedKeys=null;
let cachedUntil=0;

export async function gitlabProducerRole(req,audience) {
  const m=/^Bearer\s+(.+)$/i.exec(String(req?.headers?.authorization||''));
  const jwt=m?m[1]:'';
  if(jwt.length<200||jwt.length>16000)return '';
  const parts=jwt.split('.');
  if(parts.length!==3)return '';
  let header,claims;
  try{
    header=JSON.parse(Buffer.from(parts[0],'base64url').toString('utf8'));
    claims=JSON.parse(Buffer.from(parts[1],'base64url').toString('utf8'));
  }catch{return '';}
  if(header.alg!=='RS256'||!/^[A-Za-z0-9_.-]{1,200}$/.test(header.kid||''))return '';
  const now=Math.floor(Date.now()/1000);
  const aud=Array.isArray(claims.aud)?claims.aud:[claims.aud];
  if(claims.iss!==ISSUER||!aud.includes(audience)
    ||String(claims.project_id)!==PROJECT_ID
    ||claims.project_path!==PROJECT||claims.sub!==SUBJECT
    ||claims.ref!=='main'||claims.ref_type!=='branch'
    ||String(claims.ref_protected)!=='true'
    ||!['push','web','schedule','api'].includes(claims.pipeline_source))return '';
  if(!Number.isInteger(claims.exp)||claims.exp<=now||claims.exp>now+3600
    ||!Number.isInteger(claims.iat)||claims.iat>now+60||claims.iat<now-600
    ||(claims.nbf!==undefined&&(!Number.isInteger(claims.nbf)||claims.nbf>now+60)))return '';
  try{
    if(!cachedKeys||Date.now()>cachedUntil){
      const cfg=await fetch(ISSUER+'/.well-known/openid-configuration',{signal:AbortSignal.timeout(7500)});
      if(!cfg.ok)return '';
      const jwksUri=(await cfg.json()).jwks_uri;
      const url=new URL(jwksUri);
      if(url.origin!==ISSUER||url.username||url.password)return '';
      const keys=await fetch(jwksUri,{signal:AbortSignal.timeout(7500)});
      if(!keys.ok)return '';
      const parsed=await keys.json();
      if(!Array.isArray(parsed.keys))return '';
      cachedKeys=parsed.keys;
      cachedUntil=Date.now()+300000;
    }
    const key=cachedKeys.find(x=>x.kid===header.kid&&x.kty==='RSA'&&(!x.alg||x.alg==='RS256'));
    if(!key)return '';
    const pub=crypto.createPublicKey({key,format:'jwk'});
    return crypto.verify('RSA-SHA256',Buffer.from(parts[0]+'.'+parts[1]),pub,
      Buffer.from(parts[2],'base64url'))?'producer':'';
  }catch{return '';}
}
