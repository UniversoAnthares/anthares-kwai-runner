import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,createHmac,createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
const origin='https://anthares-ara-mcp.anthares1.workers.dev';
const cid='https://claude.ai/oauth/mcp-oauth-client-metadata';
const redirect='https://claude.ai/api/mcp/auth_callback';
const secret=Buffer.alloc(48,23).toString('base64url');
const pair=generateKeyPairSync('ed25519');
const env={ARA_OAUTH_SECRET:secret,ARA_SIGNING_PRIVATE_JWK:JSON.stringify(pair.privateKey.export({format:'jwk'})),
 ARA_SIGNING_PUBLIC_JWK:JSON.stringify(pair.publicKey.export({format:'jwk'})),ARA_OWNER_GITHUB_CLIENT_ID:'test-client',
 ARA_OWNER_GITHUB_CLIENT_SECRET:'test-client-secret',ARA_OWNER_GITHUB_ID:'81930373',AUTH_OWNER_METHOD:'github'};
let source=(await readFile(new URL('./index.js',import.meta.url),'utf8'))
 .replace('import { DurableObject } from "cloudflare:workers";','class DurableObject {}')
 .replace(/from "\.\/([^"]+\.mjs)"/g,(_,name)=>'from "'+new URL('./'+name,import.meta.url).href+'"');
const worker=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
function sign(p){const b=Buffer.from(JSON.stringify(p)).toString('base64url');return b+'.'+createHmac('sha256',Buffer.from(secret,'base64url')).update(b).digest('base64url');}
function form(path,values,headers={}){return new Request(origin+path,{method:'POST',headers:{origin,'content-type':'application/x-www-form-urlencoded',...headers},body:new URLSearchParams(values)});}
const verifier='V'.repeat(64),challenge=createHash('sha256').update(verifier).digest('base64url');
let used=new Set(),owner='81930373',ghChallenge='',ghVerifier='',providerCalls=0;
const oldFetch=globalThis.fetch;
globalThis.fetch=async(url,init={})=>{
 const u=new URL(url);
 if(u.pathname==='/v1/mcp/oauth/consume'){
  const p=JSON.parse(init.body),key=p.kind+':'+p.jti;
  if(used.has(key))return Response.json({error:'replay'},{status:409});
  used.add(key);return Response.json({ok:true});
 }
 if(u.pathname==='/v1/mcp/status')return Response.json({connected:true,backend:'test-vercel-neon'});
 if(u.href==='https://github.com/login/oauth/access_token'){
  providerCalls++;const f=new URLSearchParams(init.body);ghVerifier=f.get('code_verifier');
  assert.equal(createHash('sha256').update(ghVerifier).digest('base64url'),ghChallenge);
  assert.equal(f.get('redirect_uri'),origin+'/oauth/owner/github/callback');
  return Response.json({access_token:'fake-identity-token',scope:'',token_type:'bearer'});
 }
 if(u.href==='https://api.github.com/user')return Response.json({id:Number(owner),login:'UniversoAnthares'});
 if(init.method==='DELETE'&&u.pathname.startsWith('/applications/'))return new Response(null,{status:204});
 throw Error('unexpected_external_request');
};
async function pending(client=cid,red=redirect,scope='ara.read github.read github.write'){
 const u=new URL(origin+'/oauth/authorize');u.search=new URLSearchParams({client_id:client,redirect_uri:red,
  response_type:'code',code_challenge:challenge,code_challenge_method:'S256',scope,state:'outer-state'});
 const r=await worker.fetch(new Request(u),env);return {r,tx:(await r.text()).match(/name="tx" value="([^"]+)"/)?.[1]};
}
async function begin(tx,requestOrigin=origin){
 const r=await worker.fetch(form('/oauth/owner/github',{tx},{origin:requestOrigin}),env);
 if(r.status!==302)return {r};
 const u=new URL(r.headers.get('location'));ghChallenge=u.searchParams.get('code_challenge');
 assert.equal(u.searchParams.get('scope'),'');assert.equal(u.searchParams.get('code_challenge_method'),'S256');
 const cookie=r.headers.get('set-cookie');assert.match(cookie,/HttpOnly; Secure; SameSite=Lax/);
 assert(!cookie.includes(tx));assert(!cookie.includes('oauth_pending'));
 return {r,cookie:cookie.split(';')[0],state:u.searchParams.get('state')};
}
async function callback(p,state=p.state){return worker.fetch(new Request(origin+'/oauth/owner/github/callback?'+new URLSearchParams({state,code:'provider-code'}),{headers:p.cookie?{cookie:p.cookie}:{}}),env);}
test('owner GitHub flow preserves OAuth PKCE, single-use codes, refresh and restricted scopes',async()=>{
 const p=await pending();assert.equal(p.r.status,200);assert(p.tx);assert.equal(p.r.headers.get("referrer-policy"),"same-origin");assert(p.r.headers.get("content-security-policy").includes("form-action 'self' https://github.com https://claude.ai https://chatgpt.com;"));
 const a=await begin(p.tx);
 const bad=await callback(a,'forged-state');assert.equal(bad.status,403);assert.equal(providerCalls,0);
 const result=await callback(a);assert.equal(result.status,302);
 const red=new URL(result.headers.get('location'));assert.equal(red.origin,'https://claude.ai');
 assert.equal(red.searchParams.get('state'),'outer-state');assert.equal(red.searchParams.get('iss'),origin);
 assert.match(result.headers.get('set-cookie'),/Max-Age=0/);
 assert.equal((await callback(a)).status,409);
 const code=red.searchParams.get('code');
 let r=await worker.fetch(form('/oauth/token',{grant_type:'authorization_code',client_id:cid,redirect_uri:redirect,code,code_verifier:'X'.repeat(64)}),env);
 assert.equal(r.status,400);
 r=await worker.fetch(form('/oauth/token',{grant_type:'authorization_code',client_id:cid,redirect_uri:redirect,code,code_verifier:verifier}),env);
 assert.equal(r.status,200);const tokens=await r.json();assert.equal(tokens.scope,'ara.read github.read github.write');
 assert.equal((await worker.fetch(form('/oauth/token',{grant_type:'authorization_code',client_id:cid,redirect_uri:redirect,code,code_verifier:verifier}),env)).status,400);
 const list=await worker.fetch(new Request(origin+'/mcp',{method:'POST',headers:{authorization:'Bearer '+tokens.access_token},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list'})}),env);
 const tools=(await list.json()).result.tools;assert(tools.some(x=>x.name==='github_get_file'));assert(tools.some(x=>x.name==='github_draft_pr'));assert(!tools.some(x=>x.name==='remote_exec'));
 r=await worker.fetch(form('/oauth/token',{grant_type:'refresh_token',client_id:cid,refresh_token:tokens.refresh_token}),env);assert.equal(r.status,200);
 assert.equal((await worker.fetch(form('/oauth/token',{grant_type:'refresh_token',client_id:cid,refresh_token:tokens.refresh_token}),env)).status,400);
});
test('wrong identity, missing cookie, origin forgery and tampering fail closed',async()=>{
 const p=await pending();assert.equal((await begin(p.tx,'https://evil.example')).r.status,403);
 const a=await begin(p.tx);assert.equal((await callback({...a,cookie:''})).status,403);
 assert.equal((await callback({...a,cookie:a.cookie+'tampered'})).status,403);
 owner='123';assert.equal((await callback(a)).status,403);owner='81930373';
 assert.equal((await worker.fetch(form('/oauth/authorize',{tx:p.tx,approval:'00000000'}),env)).status,403);
});
test('expired identity cookie is rejected before provider exchange',async()=>{
 const p=await pending(),a=await begin(p.tx),now=Date.now;Date.now=()=>now()+601000;
 try{assert.equal((await callback(a)).status,403)}finally{Date.now=now}
});
test('forged callbacks, Claude remote write scope and unauthenticated MCP are rejected',async()=>{
 assert.equal((await pending(cid,'https://evil.example/callback')).r.status,400);
 const narrowed=await pending(cid,redirect,'ara.read ara.write');assert.equal(narrowed.r.status,200);assert.deepEqual(JSON.parse(Buffer.from(narrowed.tx.split('.')[0],'base64url')).scopes,['ara.read']);
 assert.equal((await pending(cid,redirect,'ara.write')).r.status,400);
 const denied=await worker.fetch(new Request(origin+'/mcp',{method:'POST',body:'{}'}),env);assert.equal(denied.status,401);assert(denied.headers.get('www-authenticate').includes('github.read github.write'));
});
test('existing pinned ChatGPT authorization and access-token contract remain valid',async()=>{
 const client='https://chatgpt.com/oauth/client.json',callback='https://chatgpt.com/connector_platform_oauth_redirect';
 const chatEnv={...env,ARA_PINNED_CLIENT:client};
 const now=Math.floor(Date.now()/1000);
 const access=sign({typ:'access',iss:origin,aud:origin,exp:now+600,cid:client,sub:'anthares-owner',scp:['ara.read','ara.write']});
 const r=await worker.fetch(new Request(origin+'/mcp',{method:'POST',headers:{authorization:'Bearer '+access},body:JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/list'})}),chatEnv);
 assert.equal(r.status,200);assert((await r.json()).result.tools.some(x=>x.name==='remote_exec'));
 const p=await pending(client,callback,'ara.read ara.write');assert.equal(p.r.status,200);
});
test.after(()=>{globalThis.fetch=oldFetch});
