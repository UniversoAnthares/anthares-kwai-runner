import {fetchWithoutRedirects} from "./secure-fetch.mjs";
// Owner identity fallback. OAuth secrets and provider tokens never enter HTML or logs.
const COOKIE = '__Host-ara-owner';
const CALLBACK = '/oauth/owner/github/callback';
const encode = b => btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
const decode = s => Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
const random = n => encode(crypto.getRandomValues(new Uint8Array(n)));
const fail = (error,status=400) => Response.json({error},{status,headers:{'cache-control':'no-store'}});
const cookie = value => COOKIE+'='+value+'; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age='+(value?'600':'0');
export function ownerGithubConfigured(env) {
  return env.AUTH_OWNER_METHOD==='github' && !!env.ARA_OWNER_GITHUB_CLIENT_ID &&
    !!env.ARA_OWNER_GITHUB_CLIENT_SECRET && /^[1-9][0-9]*$/.test(env.ARA_OWNER_GITHUB_ID||'');
}
async function key(env,h) {
  const material=await h.state(env).hmac('owner-github-cookie-aes-v1');
  return crypto.subtle.importKey('raw',decode(material),{name:'AES-GCM'},false,['encrypt','decrypt']);
}
async function seal(env,h,value) {
  const iv=crypto.getRandomValues(new Uint8Array(12));
  const encrypted=await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:new TextEncoder().encode(h.origin+CALLBACK)},await key(env,h),new TextEncoder().encode(JSON.stringify(value)));
  return encode(iv)+'.'+encode(encrypted);
}
async function unseal(env,h,value) {
  const [iv,encrypted,...rest]=String(value||'').split('.');
  if(!iv||!encrypted||rest.length)return null;
  try {
    const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:decode(iv),additionalData:new TextEncoder().encode(h.origin+CALLBACK)},await key(env,h),decode(encrypted));
    const p=JSON.parse(new TextDecoder().decode(plain));
    return p.exp>Date.now() && p.exp<=Date.now()+601000 ? p:null;
  }catch{return null;}
}
function configured(env){return ownerGithubConfigured(env);}
export async function startOwnerGithub(req,env,h) {
  if(!configured(env))return fail('owner_identity_unavailable',503);
  if(req.headers.get('origin')!==h.origin)return fail('invalid_origin',403);
  const f=await req.formData();const tx=String(f.get('tx')||'');
  if(!await h.pending(env,tx))return fail('authorization_expired');
  const verifier=random(48), nonce=random(32), exp=Date.now()+600000;
  const challenge=encode(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier)));
  const target=new URL('https://github.com/login/oauth/authorize');
  target.search=new URLSearchParams({client_id:env.ARA_OWNER_GITHUB_CLIENT_ID,redirect_uri:h.origin+CALLBACK,
    state:nonce,code_challenge:challenge,code_challenge_method:'S256',scope:'',allow_signup:'false'});
  return new Response(null,{status:302,headers:{location:target.href,'set-cookie':cookie(await seal(env,h,{tx,verifier,nonce,exp})),
    'cache-control':'no-store','referrer-policy':'no-referrer'}});
}
async function githubFetch(url,init={}) {
  return fetchWithoutRedirects(url,{...init,signal:AbortSignal.timeout(12000)});
}
export async function finishOwnerGithub(req,env,h) {
  if(!configured(env))return fail('owner_identity_unavailable',503);
  const u=new URL(req.url);
  const raw=(req.headers.get('cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith(COOKIE+'='))?.slice(COOKIE.length+1);
  const p=await unseal(env,h,raw);
  if(!p || !u.searchParams.get('state') || u.searchParams.get('state')!==p.nonce)return fail('owner_state_invalid',403);
  if(!await h.pending(env,p.tx))return fail('authorization_expired');
  if(u.searchParams.has('error') || !u.searchParams.get('code'))return fail('owner_authorization_denied',403);
  // A replay is a confirmed duplicate; a failed replay-store request remains retryable.
  let callbackConsumed;
  try { callbackConsumed=await h.state(env).consume('oauth_owner_callback',p.nonce,Math.floor(p.exp/1000)); }
  catch { return fail('owner_control_unavailable',503); }
  if(!callbackConsumed)return fail('owner_callback_replayed',409);
  let access='',stage='provider_token';
  try {
    const r=await githubFetch('https://github.com/login/oauth/access_token',{method:'POST',
      headers:{accept:'application/json','content-type':'application/x-www-form-urlencoded'},
      body:new URLSearchParams({client_id:env.ARA_OWNER_GITHUB_CLIENT_ID,client_secret:env.ARA_OWNER_GITHUB_CLIENT_SECRET,
        redirect_uri:h.origin+CALLBACK,code:u.searchParams.get('code'),code_verifier:p.verifier})});
    const t=await r.json();
    if(!r.ok||!t.access_token||t.error)return fail('owner_provider_exchange_failed',403);
    access=t.access_token;
    if(t.scope && String(t.scope).trim())return fail('owner_provider_unexpected_scope',403);
    stage='provider_identity';
    const user=await githubFetch('https://api.github.com/user',{headers:{authorization:'Bearer '+access,
      accept:'application/vnd.github+json','user-agent':'Anthares-Owner-Identity','X-GitHub-Api-Version':'2022-11-28'}});
    const identity=await user.json();
    if(!user.ok || String(identity.id)!==String(env.ARA_OWNER_GITHUB_ID))return fail('owner_identity_denied',403);
    stage="authorization_code";
    const result=await h.complete(env,p.tx);
    result.headers.set('set-cookie',cookie(''));
    return result;
  } catch (error) {
    const kind=['TypeError','AbortError','TimeoutError'].includes(error?.name)?error.name:'Error';
    console.error('oauth_owner_failure stage='+stage+' kind='+kind);
    return Response.json({error:'owner_provider_unavailable',stage},{status:503,headers:{'cache-control':'no-store'}});
  } finally {
    // The identity-only provider credential is ephemeral; revoke without persisting it.
    if(access)try{
      await fetchWithoutRedirects('https://api.github.com/applications/'+env.ARA_OWNER_GITHUB_CLIENT_ID+'/token',{
        method:'DELETE',headers:{authorization:'Basic '+btoa(env.ARA_OWNER_GITHUB_CLIENT_ID+':'+env.ARA_OWNER_GITHUB_CLIENT_SECRET),
          accept:'application/vnd.github+json','content-type':'application/json','user-agent':'Anthares-Owner-Identity'},
        body:JSON.stringify({access_token:access}),signal:AbortSignal.timeout(3000)});
    }catch{ /* Identity token is never retained even when revocation is temporarily unavailable. */ }
  }
}
