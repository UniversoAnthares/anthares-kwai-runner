import { spawn } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { setTimeout as sleep } from 'node:timers/promises';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const port=3120, internal=3121;
const origin=`http://127.0.0.1:${port}`;
const password='qa-password-0123456789-strong';
const clientId='https://chatgpt.com/oauth/client.json';
const redirectUri='https://chatgpt.com/connector_platform_oauth_redirect';
const child=spawn(process.execPath,['gateway.mjs'],{
  cwd:new URL('.',import.meta.url),
  env:{...process.env,PORT:String(port),ARA_INTERNAL_MCP_PORT:String(internal),ARA_PUBLIC_URL:origin,
    ARA_OAUTH_ADMIN_PASSWORD:password,ARA_OAUTH_TOKEN_SECRET:'qa-token-secret-0123456789-abcdefghijklmnopqrstuvwxyz',
    ARA_SHARED:'qa-control-secret-0123456789-abcdefghijklmnopqrstuvwxyz',ANTHARES_CONTROL_URL:'http://127.0.0.1:9'},
  stdio:['ignore','pipe','pipe']
});
let stderr=''; child.stderr.on('data',c=>stderr+=c.toString());
function assert(ok,msg){if(!ok)throw new Error(msg)}
async function ready(){for(let i=0;i<80;i++){try{const r=await fetch(`${origin}/health`);if(r.status===200)return}catch{} await sleep(100)}throw new Error(`gateway not ready ${stderr}`)}
function pkce(verifier){return createHash('sha256').update(verifier).digest('base64url')}
async function authorize(scope='ara.read ara.write'){
  const verifier=randomBytes(48).toString('base64url'); const challenge=pkce(verifier); const state=randomBytes(8).toString('hex');
  const q=new URLSearchParams({response_type:'code',client_id:clientId,redirect_uri:redirectUri,code_challenge:challenge,code_challenge_method:'S256',resource:origin,scope,state});
  const page=await fetch(`${origin}/oauth/authorize?${q}`); assert(page.status===200,'authorize page failed');
  const html=await page.text(); const m=/name="tx" value="([^"]+)"/.exec(html); assert(m,'authorization transaction missing');
  const denied=await fetch(`${origin}/oauth/authorize`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({tx:m[1],password:'wrong-password'}),redirect:'manual'}); assert(denied.status===403,'wrong password was not denied');
  const ok=await fetch(`${origin}/oauth/authorize`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({tx:m[1],password}),redirect:'manual'}); assert(ok.status===302,'authorization approval failed');
  const location=new URL(ok.headers.get('location')); assert(location.origin==='https://chatgpt.com','unexpected redirect origin'); assert(location.searchParams.get('state')===state,'state mismatch'); assert(location.searchParams.get('iss')===origin,'issuer mismatch');
  const code=location.searchParams.get('code'); assert(code,'authorization code missing');
  const token=await fetch(`${origin}/oauth/token`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'authorization_code',client_id:clientId,redirect_uri:redirectUri,code,code_verifier:verifier,resource:origin})});
  assert(token.status===200,`token exchange failed ${token.status}`); return token.json();
}
try{
  await ready();
  const prm=await fetch(`${origin}/.well-known/oauth-protected-resource`); const prmBody=await prm.json(); assert(prm.status===200&&prmBody.resource===origin,'protected resource metadata failed');
  const asm=await fetch(`${origin}/.well-known/oauth-authorization-server`); const asmBody=await asm.json(); assert(asm.status===200&&asmBody.code_challenge_methods_supported.includes('S256')&&asmBody.client_id_metadata_document_supported===true,'authorization metadata failed');
  const unauth=await fetch(`${origin}/mcp`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}); assert(unauth.status===401&&(unauth.headers.get('www-authenticate')||'').includes('resource_metadata'),'OAuth challenge missing');
  const tokens=await authorize(); assert(tokens.access_token&&tokens.refresh_token&&tokens.scope.includes('ara.write'),'full tokens missing');
  const transport=new StreamableHTTPClientTransport(new URL(`${origin}/mcp`),{requestInit:{headers:{Authorization:`Bearer ${tokens.access_token}`}}});
  const client=new Client({name:'ara-oauth-qa',version:'1.0.0'}); await client.connect(transport); const listed=await client.listTools(); assert(listed.tools.length>=19,`expected >=19 tools, got ${listed.tools.length}`); await client.close();
  const refresh=await fetch(`${origin}/oauth/token`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'refresh_token',client_id:clientId,refresh_token:tokens.refresh_token})}); assert(refresh.status===200&&(await refresh.json()).access_token,'refresh token failed');
  const readTokens=await authorize('ara.read');
  const writeAttempt=await fetch(`${origin}/mcp`,{method:'POST',headers:{Authorization:`Bearer ${readTokens.access_token}`,'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:77,method:'tools/call',params:{name:'remote_exec',arguments:{command:'whoami'}}})}); assert(writeAttempt.status===403,'read-only token reached write tool');
  console.log(JSON.stringify({ok:true,tests:9,oauth:'PKCE+refresh',scope_enforcement:true,tools:listed.tools.length},null,2));
} finally { child.kill('SIGTERM'); }
