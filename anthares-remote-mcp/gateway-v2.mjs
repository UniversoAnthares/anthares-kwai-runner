import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { createHash, createHmac, generateKeyPairSync, randomBytes, sign, timingSafeEqual } from 'node:crypto';

const PUBLIC_ORIGIN=(process.env.ARA_PUBLIC_URL||'https://anthares-remote-mcp.onrender.com').replace(/\/$/,'');
const PUBLIC_PORT=Number(process.env.PORT||3000);
const INTERNAL_PORT=Number(process.env.ARA_INTERNAL_MCP_PORT||3118);
const CONTROL_URL=(process.env.ANTHARES_CONTROL_URL||'https://anthares-remote-control.onrender.com').replace(/\/$/,'');
const DEVICE_ID=process.env.ANTHARES_DEVICE_ID||'DESKTOP-FTDK0HP';
const TOKEN_SECRET=process.env.ARA_OAUTH_TOKEN_SECRET||'';
const SCOPES=new Set(['ara.read','ara.write']);
const WRITE_TOOLS=new Set(['remote_exec','clipboard_set','file_write','file_write_chunk','remote_job_start','remote_job_cancel','process_start','process_kill','service_start','service_stop','file_mkdir','file_remove','file_rename','file_copy','file_write_atomic']);
const transactions=new Map();
const codes=new Map();
const rate=new Map();
const pair=generateKeyPairSync('ed25519');
const privateDer=pair.privateKey.export({type:'pkcs8',format:'der'}).toString('base64');
const publicPem=String(pair.publicKey.export({type:'spki',format:'pem'}));
const internalToken=randomBytes(48).toString('base64url');

function safeEq(a,b){const aa=Buffer.from(String(a));const bb=Buffer.from(String(b));return aa.length===bb.length&&timingSafeEqual(aa,bb);}
function b64url(v){return Buffer.from(v).toString('base64url');}
function sha256(v){return createHash('sha256').update(v).digest();}
function json(res,status,body,headers={}){res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store',...headers});res.end(JSON.stringify(body));}
function form(buf){return new URLSearchParams(buf.toString('utf8'));}
function esc(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function readBody(req,max=3*1024*1024){const chunks=[];let n=0;for await(const c of req){n+=c.length;if(n>max)throw new Error('request_too_large');chunks.push(c);}return Buffer.concat(chunks);}
function validateClientId(v){return v==='https://chatgpt.com/oauth/client.json'||/^https:\/\/chatgpt\.com\/oauth\/[A-Za-z0-9_-]{8,}\/client\.json$/.test(v||'');}
function validateRedirect(v){return v==='https://chatgpt.com/connector_platform_oauth_redirect'||/^https:\/\/chatgpt\.com\/connector\/oauth\/[A-Za-z0-9_-]+$/.test(v||'');}
function parseScopes(v){const xs=String(v||'ara.read ara.write').trim().split(/\s+/).filter(Boolean);if(!xs.length||xs.some(x=>!SCOPES.has(x)))return null;return [...new Set(xs)];}
function signToken(payload){if(TOKEN_SECRET.length<32)throw new Error('oauth_not_configured');const body=b64url(JSON.stringify(payload));const sig=createHmac('sha256',TOKEN_SECRET).update(body).digest('base64url');return `${body}.${sig}`;}
function verifyToken(token,type){if(TOKEN_SECRET.length<32||!token)return null;const [body,sig,extra]=String(token).split('.');if(!body||!sig||extra)return null;const expected=createHmac('sha256',TOKEN_SECRET).update(body).digest('base64url');if(!safeEq(sig,expected))return null;try{const p=JSON.parse(Buffer.from(body,'base64url').toString('utf8'));if(p.typ!==type||p.iss!==PUBLIC_ORIGIN||p.aud!==PUBLIC_ORIGIN||p.exp<=Math.floor(Date.now()/1000)||!Array.isArray(p.scp))return null;return p;}catch{return null;}}
function issueTokens(clientId,scopes){const now=Math.floor(Date.now()/1000);const base={iss:PUBLIC_ORIGIN,aud:PUBLIC_ORIGIN,sub:'anthares-owner',cid:clientId,scp:scopes};return{access_token:signToken({...base,typ:'access',iat:now,exp:now+900,jti:randomBytes(16).toString('hex')}),token_type:'Bearer',expires_in:900,refresh_token:signToken({...base,typ:'refresh',iat:now,exp:now+30*24*3600,jti:randomBytes(16).toString('hex')}),scope:scopes.join(' ')}};
function bearer(req){const m=/^Bearer\s+(.+)$/i.exec(req.headers.authorization||'');return m?m[1]:'';}
function challenge(){return `Bearer resource_metadata="${PUBLIC_ORIGIN}/.well-known/oauth-protected-resource", scope="ara.read ara.write"`;}
function signControl(method,path,raw=''){const ts=String(Date.now());const payload=`${ts}\n${method.toUpperCase()}\n${path}\n${raw}`;return{ts,sig:sign(null,Buffer.from(payload),pair.privateKey).toString('base64url')}};
async function control(path,{method='GET',body,timeoutMs=30000}={}){const raw=body===undefined?'':JSON.stringify(body);const s=signControl(method,path,raw);return fetch(`${CONTROL_URL}${path}`,{method,headers:{'Content-Type':'application/json','X-ARA-Timestamp':s.ts,'X-ARA-Signature':s.sig,'X-ARA-Signer':'anthares-remote-mcp'},body:body===undefined?undefined:raw,signal:AbortSignal.timeout(timeoutMs)});}
async function sendApprovalCode(code){const r=await control('/v1/mcp/execute',{method:'POST',timeoutMs:30000,body:{device_id:DEVICE_ID,type:'clipboard_set',args:{text:code},timeout_seconds:20}});return r.ok;}
function checkRate(p,write){const key=`${p.jti}:${write?'w':'r'}`;const now=Date.now();const max=write?30:120;let x=rate.get(key);if(!x||x.reset<now)x={count:0,reset:now+60000};x.count++;rate.set(key,x);return x.count<=max;}
setInterval(()=>{const now=Date.now();for(const[k,v]of transactions)if(v.expires<now)transactions.delete(k);for(const[k,v]of codes)if(v.expires<now)codes.delete(k);for(const[k,v]of rate)if(v.reset<now)rate.delete(k);},60000).unref();

const child=spawn(process.execPath,['remote-server.mjs'],{cwd:new URL('.',import.meta.url),env:{...process.env,ARA_INTERNAL_MCP_PORT:String(INTERNAL_PORT),ARA_MCP_CLIENT_TOKEN:internalToken,ARA_CONTROL_PRIVATE_KEY_B64:privateDer,ANTHARES_CONTROL_URL:CONTROL_URL,ANTHARES_DEVICE_ID:DEVICE_ID},stdio:['ignore','inherit','inherit']});
child.on('exit',code=>{console.error(`signed remote MCP exited code=${code}`);process.exit(code||1);});
for(const sig of ['SIGTERM','SIGINT'])process.on(sig,()=>{child.kill(sig);process.exit(0);});

async function internalHealth(){try{const r=await fetch(`http://127.0.0.1:${INTERNAL_PORT}/health`,{signal:AbortSignal.timeout(1500)});return r.ok;}catch{return false;}}
async function controlHealth(){try{const path=`/v1/mcp/status?device_id=${encodeURIComponent(DEVICE_ID)}`;const r=await control(path,{timeoutMs:7000});return r.ok;}catch{return false;}}
function metadata(res){json(res,200,{issuer:PUBLIC_ORIGIN,authorization_endpoint:`${PUBLIC_ORIGIN}/oauth/authorize`,token_endpoint:`${PUBLIC_ORIGIN}/oauth/token`,response_types_supported:['code'],grant_types_supported:['authorization_code','refresh_token'],code_challenge_methods_supported:['S256'],token_endpoint_auth_methods_supported:['none'],scopes_supported:[...SCOPES],client_id_metadata_document_supported:true,authorization_response_iss_parameter_supported:true});}

const server=createServer(async(req,res)=>{try{
  const u=new URL(req.url,PUBLIC_ORIGIN);
  if(req.method==='GET'&&u.pathname==='/health'){const[ih,ch]=await Promise.all([internalHealth(),controlHealth()]);const oauth=TOKEN_SECRET.length>=32;json(res,ih&&ch&&oauth?200:503,{ok:ih&&ch&&oauth,service:'anthares-remote-mcp-gateway-v2',oauth:oauth?'configured':'pending',control:ch?'signed-ready':'pending',mcp:ih?'ready':'pending'});return;}
  if(req.method==='GET'&&u.pathname==='/.well-known/ara-control-key'){res.writeHead(200,{'Content-Type':'application/x-pem-file','Cache-Control':'no-store'});res.end(publicPem);return;}
  if(req.method==='GET'&&u.pathname==='/.well-known/oauth-protected-resource'){json(res,200,{resource:PUBLIC_ORIGIN,authorization_servers:[PUBLIC_ORIGIN],scopes_supported:[...SCOPES],resource_documentation:'https://github.com/UniversoAnthares/anthares-kwai-runner'});return;}
  if(req.method==='GET'&&(u.pathname==='/.well-known/oauth-authorization-server'||u.pathname==='/.well-known/openid-configuration')){metadata(res);return;}
  if(req.method==='GET'&&u.pathname==='/oauth/authorize'){
    if(TOKEN_SECRET.length<32){json(res,503,{error:'oauth_not_configured'});return;}
    const clientId=u.searchParams.get('client_id')||'',redirectUri=u.searchParams.get('redirect_uri')||'',responseType=u.searchParams.get('response_type')||'',challengeCode=u.searchParams.get('code_challenge')||'',method=u.searchParams.get('code_challenge_method')||'',resource=u.searchParams.get('resource')||PUBLIC_ORIGIN,scopes=parseScopes(u.searchParams.get('scope'));
    if(!validateClientId(clientId)||!validateRedirect(redirectUri)||responseType!=='code'||method!=='S256'||challengeCode.length<43||resource!==PUBLIC_ORIGIN||!scopes){json(res,400,{error:'invalid_request'});return;}
    const approval=randomBytes(9).toString('base64url');const tx=signToken({typ:'oauth_pending',iss:PUBLIC_ORIGIN,aud:PUBLIC_ORIGIN,exp:Math.floor(Date.now()/1000)+600,jti:randomBytes(16).toString('hex'),clientId,redirectUri,challenge:challengeCode,resource,scopes,scp:scopes,state:u.searchParams.get('state')||'',approvalHash:createHash('sha256').update(approval).digest('hex')});
    if(!(await sendApprovalCode(approval))){json(res,503,{error:'device_authorization_unavailable'});return;}
    // Pending OAuth transactions are signed and survive a gateway process restart.
    const html=`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Remote Agent</title></head><body><main><h1>Anthares Remote Agent</h1><p>Um código de autorização foi colocado no clipboard do computador cadastrado. Cole-o abaixo para autorizar o ChatGPT.</p><p>Escopos: ${esc(scopes.join(', '))}</p><form method="post" action="/oauth/authorize"><input type="hidden" name="tx" value="${esc(tx)}"><label>Código <input type="password" name="approval" autocomplete="one-time-code" required autofocus></label><button type="submit">Autorizar</button></form></main></body></html>`;
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",'Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'});res.end(html);return;
  }
  if(req.method==='POST'&&u.pathname==='/oauth/authorize'){
    const body=form(await readBody(req,65536));const tx=body.get('tx')||'',approval=body.get('approval')||'';const p=verifyToken(tx,'oauth_pending');
    if(!p||p.expires<Date.now()){transactions.delete(tx);json(res,400,{error:'authorization_expired'});return;}
    if(!safeEq(createHash('sha256').update(approval).digest('hex'),p.approvalHash)){json(res,403,{error:'authorization_denied'});return;}
    transactions.delete(tx);const code=randomBytes(32).toString('base64url');codes.set(code,{...p,approval:undefined,expires:Date.now()+5*60000});const target=new URL(p.redirectUri);target.searchParams.set('code',code);if(p.state)target.searchParams.set('state',p.state);target.searchParams.set('iss',PUBLIC_ORIGIN);res.writeHead(302,{Location:target.toString(),'Cache-Control':'no-store','Referrer-Policy':'no-referrer'});res.end();return;
  }
  if(req.method==='POST'&&u.pathname==='/oauth/token'){
    const body=form(await readBody(req,131072)),grant=body.get('grant_type')||'',clientId=body.get('client_id')||'';if(!validateClientId(clientId)){json(res,400,{error:'invalid_client'});return;}
    if(grant==='authorization_code'){const code=body.get('code')||'',p=codes.get(code);codes.delete(code);if(!p||p.expires<Date.now()||p.clientId!==clientId||p.redirectUri!==(body.get('redirect_uri')||'')){json(res,400,{error:'invalid_grant'});return;}const verifier=body.get('code_verifier')||'';if(verifier.length<43||!safeEq(sha256(verifier).toString('base64url'),p.challenge)){json(res,400,{error:'invalid_grant'});return;}json(res,200,issueTokens(clientId,p.scopes));return;}
    if(grant==='refresh_token'){const p=verifyToken(body.get('refresh_token')||'','refresh');if(!p||p.cid!==clientId){json(res,400,{error:'invalid_grant'});return;}json(res,200,issueTokens(clientId,p.scp));return;}
    json(res,400,{error:'unsupported_grant_type'});return;
  }
  if(u.pathname==='/mcp'){
    if(req.method!=='POST'){res.writeHead(405,{Allow:'POST'});res.end();return;}
    const token=verifyToken(bearer(req),'access');if(!token){json(res,401,{error:'unauthorized'},{'WWW-Authenticate':challenge()});return;}
    const raw=await readBody(req);let rpc;try{rpc=JSON.parse(raw.toString('utf8'));}catch{json(res,400,{error:'invalid_json'});return;}
    const tool=rpc&&!Array.isArray(rpc)&&rpc.method==='tools/call'&&typeof rpc.params?.name==='string'?rpc.params.name:'';const write=WRITE_TOOLS.has(tool),required=write?'ara.write':'ara.read';if(!token.scp.includes(required)){json(res,403,{error:'insufficient_scope',required_scope:required},{'WWW-Authenticate':challenge()});return;}if(!checkRate(token,write)){json(res,429,{error:'rate_limited'});return;}
    const headers={Authorization:`Bearer ${internalToken}`,'Content-Type':req.headers['content-type']||'application/json',Accept:req.headers.accept||'application/json, text/event-stream'};if(req.headers['mcp-protocol-version'])headers['MCP-Protocol-Version']=req.headers['mcp-protocol-version'];
    const upstream=await fetch(`http://127.0.0.1:${INTERNAL_PORT}/mcp`,{method:'POST',headers,body:raw,signal:AbortSignal.timeout(150000)});const out=Buffer.from(await upstream.arrayBuffer());const responseHeaders={'Content-Type':upstream.headers.get('content-type')||'application/json','Cache-Control':'no-store'};res.writeHead(upstream.status,responseHeaders);res.end(out);return;
  }
  res.writeHead(404);res.end();
}catch(e){console.error('gateway-v2 error',e?.message||e);if(!res.headersSent)json(res,e?.message==='request_too_large'?413:500,{error:'gateway_error'});else res.end();}});
server.requestTimeout=160000;
server.listen(PUBLIC_PORT,'0.0.0.0',()=>console.log(`Anthares signed OAuth gateway listening on ${PUBLIC_PORT}`));
