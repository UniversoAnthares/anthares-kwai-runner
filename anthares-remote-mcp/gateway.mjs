import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { createHash, createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

const PUBLIC_ORIGIN = (process.env.ARA_PUBLIC_URL || 'https://anthares-remote-mcp.onrender.com').replace(/\/$/, '');
const PUBLIC_PORT = Number(process.env.PORT || 3000);
const INTERNAL_PORT = Number(process.env.ARA_INTERNAL_MCP_PORT || 3118);
const ADMIN_PASSWORD = process.env.ARA_OAUTH_ADMIN_PASSWORD || '';
const TOKEN_SECRET = process.env.ARA_OAUTH_TOKEN_SECRET || '';
const CONTROL_TOKEN = process.env.ARA_SHARED || '';
const CONTROL_URL = process.env.ANTHARES_CONTROL_URL || 'https://anthares-remote-control.onrender.com';
const SCOPES = new Set(['ara.read', 'ara.write']);
const WRITE_TOOLS = new Set([
  'remote_exec','clipboard_set','file_write','file_write_chunk','remote_job_start','remote_job_cancel',
  'process_start','process_kill','service_start','service_stop','file_mkdir','file_remove','file_rename',
  'file_copy','file_write_atomic'
]);
const transactions = new Map();
const codes = new Map();
const rate = new Map();
const loginRate = new Map();

function b64url(input) { return Buffer.from(input).toString('base64url'); }
function sha256(text) { return createHash('sha256').update(text).digest(); }
function safeEq(a, b) {
  const aa = Buffer.from(String(a)); const bb = Buffer.from(String(b));
  return aa.length === bb.length && timingSafeEqual(aa, bb);
}
function json(res, status, body, headers = {}) {
  res.writeHead(status, { 'Content-Type':'application/json', 'Cache-Control':'no-store', ...headers });
  res.end(JSON.stringify(body));
}
function oauthChallenge() {
  return `Bearer resource_metadata="${PUBLIC_ORIGIN}/.well-known/oauth-protected-resource", scope="ara.read ara.write"`;
}
function cleanup() {
  const now = Date.now();
  for (const [k,v] of transactions) if (v.expires < now) transactions.delete(k);
  for (const [k,v] of codes) if (v.expires < now) codes.delete(k);
  for (const [k,v] of rate) if (v.reset < now) rate.delete(k);
  for (const [k,v] of loginRate) if (v.reset < now) loginRate.delete(k);
}
setInterval(cleanup, 60_000).unref();

function validateClientId(value) {
  if (value === 'https://chatgpt.com/oauth/client.json') return true;
  return /^https:\/\/chatgpt\.com\/oauth\/[A-Za-z0-9_-]{8,}\/client\.json$/.test(value || '');
}
function validateRedirect(value) {
  if (value === 'https://chatgpt.com/connector_platform_oauth_redirect') return true;
  return /^https:\/\/chatgpt\.com\/connector\/oauth\/[A-Za-z0-9_-]+$/.test(value || '');
}
function parseScopes(value) {
  const requested = String(value || 'ara.read ara.write').trim().split(/\s+/).filter(Boolean);
  if (!requested.length || requested.some(x => !SCOPES.has(x))) return null;
  return [...new Set(requested)];
}
function signToken(payload) {
  if (!TOKEN_SECRET) throw new Error('OAuth token secret is not configured');
  const body = b64url(JSON.stringify(payload));
  const sig = createHmac('sha256', TOKEN_SECRET).update(body).digest('base64url');
  return `${body}.${sig}`;
}
function verifyToken(token, type) {
  if (!TOKEN_SECRET || !token) return null;
  const [body, sig, extra] = String(token).split('.');
  if (!body || !sig || extra) return null;
  const expected = createHmac('sha256', TOKEN_SECRET).update(body).digest('base64url');
  if (!safeEq(sig, expected)) return null;
  try {
    const p = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
    if (p.typ !== type || p.iss !== PUBLIC_ORIGIN || p.aud !== PUBLIC_ORIGIN) return null;
    if (!Number.isFinite(p.exp) || p.exp <= Math.floor(Date.now()/1000)) return null;
    if (!Array.isArray(p.scp) || p.scp.some(x => !SCOPES.has(x))) return null;
    return p;
  } catch { return null; }
}
function issueTokens(clientId, scopes) {
  const now = Math.floor(Date.now()/1000);
  const base = { iss:PUBLIC_ORIGIN, aud:PUBLIC_ORIGIN, sub:'anthares-owner', cid:clientId, scp:scopes };
  return {
    access_token: signToken({ ...base, typ:'access', iat:now, exp:now+900, jti:randomBytes(16).toString('hex') }),
    token_type:'Bearer', expires_in:900,
    refresh_token: signToken({ ...base, typ:'refresh', iat:now, exp:now+30*24*3600, jti:randomBytes(16).toString('hex') }),
    scope: scopes.join(' '),
  };
}
function getBearer(req) {
  const m = /^Bearer\s+(.+)$/i.exec(req.headers.authorization || '');
  return m ? m[1] : '';
}
function checkRate(tokenPayload, write) {
  const key = `${tokenPayload.jti}:${write?'w':'r'}`;
  const now = Date.now();
  const max = write ? 30 : 120;
  let item = rate.get(key);
  if (!item || item.reset < now) item = { count:0, reset:now+60_000 };
  item.count++; rate.set(key, item);
  return item.count <= max;
}
function loginAllowed(req) {
  const ip = String(req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();
  const now = Date.now();
  let item = loginRate.get(ip);
  if (!item || item.reset < now) item = { count:0, reset:now+15*60_000 };
  item.count++; loginRate.set(ip, item);
  return item.count <= 12;
}
async function readBody(req, max=3*1024*1024) {
  const chunks=[]; let size=0;
  for await (const c of req) { size += c.length; if (size > max) throw new Error('request_too_large'); chunks.push(c); }
  return Buffer.concat(chunks);
}
function formBody(buf) { return new URLSearchParams(buf.toString('utf8')); }
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

const internalToken = randomBytes(48).toString('base64url');
const child = spawn(process.execPath, ['server.mjs'], {
  cwd: new URL('.', import.meta.url),
  env: {
    ...process.env,
    PORT:String(INTERNAL_PORT), ARA_MCP_TRANSPORT:'http', ARA_MCP_CLIENT_TOKEN:internalToken,
    ARA_SHARED:CONTROL_TOKEN, ANTHARES_CONTROL_URL:CONTROL_URL,
  },
  stdio:['ignore','inherit','inherit'],
});
child.on('exit', code => { console.error(`internal MCP exited code=${code}`); process.exit(code || 1); });
process.on('SIGTERM', () => { child.kill('SIGTERM'); process.exit(0); });
process.on('SIGINT', () => { child.kill('SIGINT'); process.exit(0); });

async function internalHealth() {
  try {
    const r = await fetch(`http://127.0.0.1:${INTERNAL_PORT}/health`, { signal:AbortSignal.timeout(1500) });
    const body = await r.json().catch(()=>({}));
    return { ok:r.ok && body.ok === true, body };
  } catch { return { ok:false, body:{} }; }
}

function metadata(res) {
  json(res, 200, {
    issuer: PUBLIC_ORIGIN,
    authorization_endpoint: `${PUBLIC_ORIGIN}/oauth/authorize`,
    token_endpoint: `${PUBLIC_ORIGIN}/oauth/token`,
    response_types_supported:['code'],
    grant_types_supported:['authorization_code','refresh_token'],
    code_challenge_methods_supported:['S256'],
    token_endpoint_auth_methods_supported:['none'],
    scopes_supported:[...SCOPES],
    client_id_metadata_document_supported:true,
    authorization_response_iss_parameter_supported:true,
  });
}

const server = createServer(async (req,res) => {
  try {
    const u = new URL(req.url, PUBLIC_ORIGIN);
    if (req.method === 'GET' && u.pathname === '/health') {
      const ih = await internalHealth();
      const oauthConfigured = ADMIN_PASSWORD.length >= 16 && TOKEN_SECRET.length >= 32;
      json(res, ih.ok && oauthConfigured ? 200 : 503, {
        ok:ih.ok && oauthConfigured,
        service:'anthares-remote-mcp-gateway', oauth:oauthConfigured?'configured':'pending',
        control:CONTROL_TOKEN?'configured':'pending', mcp:ih.ok?'ready':'pending'
      }); return;
    }
    if (req.method === 'GET' && u.pathname === '/.well-known/oauth-protected-resource') {
      json(res, 200, {
        resource:PUBLIC_ORIGIN, authorization_servers:[PUBLIC_ORIGIN], scopes_supported:[...SCOPES],
        resource_documentation:'https://github.com/UniversoAnthares/anthares-kwai-runner'
      }); return;
    }
    if (req.method === 'GET' && (u.pathname === '/.well-known/oauth-authorization-server' || u.pathname === '/.well-known/openid-configuration')) {
      metadata(res); return;
    }
    if (req.method === 'GET' && u.pathname === '/oauth/authorize') {
      if (ADMIN_PASSWORD.length < 16 || TOKEN_SECRET.length < 32) { json(res,503,{error:'oauth_not_configured'}); return; }
      const clientId=u.searchParams.get('client_id')||'';
      const redirectUri=u.searchParams.get('redirect_uri')||'';
      const responseType=u.searchParams.get('response_type')||'';
      const challenge=u.searchParams.get('code_challenge')||'';
      const method=u.searchParams.get('code_challenge_method')||'';
      const resource=u.searchParams.get('resource')||PUBLIC_ORIGIN;
      const scopes=parseScopes(u.searchParams.get('scope'));
      if (!validateClientId(clientId) || !validateRedirect(redirectUri) || responseType!=='code' || method!=='S256' || challenge.length<43 || resource!==PUBLIC_ORIGIN || !scopes) {
        json(res,400,{error:'invalid_request'}); return;
      }
      const tx=randomBytes(24).toString('base64url');
      transactions.set(tx,{ clientId,redirectUri,challenge,resource,scopes,state:u.searchParams.get('state')||'',expires:Date.now()+10*60_000 });
      const html=`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Anthares Remote Agent</title></head><body><main><h1>Anthares Remote Agent</h1><p>Autorizar o ChatGPT a acessar o computador cadastrado.</p><p>Escopos: ${escapeHtml(scopes.join(', '))}</p><form method="post" action="/oauth/authorize"><input type="hidden" name="tx" value="${escapeHtml(tx)}"><label>Senha de autorização <input type="password" name="password" autocomplete="current-password" required></label><button type="submit">Autorizar</button></form></main></body></html>`;
      res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'}); res.end(html); return;
    }
    if (req.method === 'POST' && u.pathname === '/oauth/authorize') {
      if (!loginAllowed(req)) { json(res,429,{error:'too_many_attempts'}); return; }
      const body=formBody(await readBody(req,64*1024));
      const tx=body.get('tx')||''; const password=body.get('password')||'';
      const pending=transactions.get(tx);
      if (!pending || pending.expires<Date.now()) { transactions.delete(tx); json(res,400,{error:'authorization_expired'}); return; }
      if (!safeEq(password,ADMIN_PASSWORD)) { json(res,403,{error:'authorization_denied'}); return; }
      transactions.delete(tx);
      const code=randomBytes(32).toString('base64url');
      codes.set(code,{...pending,expires:Date.now()+5*60_000});
      const target=new URL(pending.redirectUri); target.searchParams.set('code',code); if(pending.state) target.searchParams.set('state',pending.state); target.searchParams.set('iss',PUBLIC_ORIGIN);
      res.writeHead(302,{Location:target.toString(),'Cache-Control':'no-store','Referrer-Policy':'no-referrer'}); res.end(); return;
    }
    if (req.method === 'POST' && u.pathname === '/oauth/token') {
      const body=formBody(await readBody(req,128*1024)); const grant=body.get('grant_type')||''; const clientId=body.get('client_id')||'';
      if (!validateClientId(clientId)) { json(res,400,{error:'invalid_client'}); return; }
      if (grant === 'authorization_code') {
        const code=body.get('code')||''; const pending=codes.get(code); codes.delete(code);
        if (!pending || pending.expires<Date.now() || pending.clientId!==clientId || pending.redirectUri!==(body.get('redirect_uri')||'')) { json(res,400,{error:'invalid_grant'}); return; }
        const verifier=body.get('code_verifier')||''; const computed=sha256(verifier).toString('base64url');
        if (verifier.length<43 || !safeEq(computed,pending.challenge)) { json(res,400,{error:'invalid_grant'}); return; }
        const resource=body.get('resource')||PUBLIC_ORIGIN; if(resource!==PUBLIC_ORIGIN){json(res,400,{error:'invalid_target'});return;}
        json(res,200,issueTokens(clientId,pending.scopes)); return;
      }
      if (grant === 'refresh_token') {
        const p=verifyToken(body.get('refresh_token')||'','refresh');
        if (!p || p.cid!==clientId) { json(res,400,{error:'invalid_grant'}); return; }
        json(res,200,issueTokens(clientId,p.scp)); return;
      }
      json(res,400,{error:'unsupported_grant_type'}); return;
    }
    if (u.pathname === '/mcp') {
      if (req.method !== 'POST') { res.writeHead(405,{Allow:'POST'}); res.end(); return; }
      const token=verifyToken(getBearer(req),'access');
      if (!token) { json(res,401,{error:'unauthorized'},{'WWW-Authenticate':oauthChallenge()}); return; }
      const raw=await readBody(req);
      let rpc; try { rpc=JSON.parse(raw.toString('utf8')); } catch { json(res,400,{error:'invalid_json'}); return; }
      const call = rpc && !Array.isArray(rpc) && rpc.method==='tools/call' ? rpc.params : null;
      const tool=call && typeof call.name==='string' ? call.name : '';
      const write=WRITE_TOOLS.has(tool);
      const required=write?'ara.write':'ara.read';
      if ((tool || rpc?.method==='tools/list' || rpc?.method==='initialize') && !token.scp.includes(required)) {
        json(res,403,{error:'insufficient_scope',required_scope:required},{'WWW-Authenticate':oauthChallenge()}); return;
      }
      if (!checkRate(token,write)) { json(res,429,{error:'rate_limited'}); return; }
      const headers={ 'Authorization':`Bearer ${internalToken}`, 'Content-Type':req.headers['content-type']||'application/json', 'Accept':req.headers.accept||'application/json, text/event-stream' };
      if(req.headers['mcp-protocol-version']) headers['MCP-Protocol-Version']=req.headers['mcp-protocol-version'];
      const upstream=await fetch(`http://127.0.0.1:${INTERNAL_PORT}/mcp`,{method:'POST',headers,body:raw,signal:AbortSignal.timeout(145000)});
      const out=Buffer.from(await upstream.arrayBuffer());
      const responseHeaders={'Content-Type':upstream.headers.get('content-type')||'application/json','Cache-Control':'no-store'};
      const sid=upstream.headers.get('mcp-session-id'); if(sid) responseHeaders['MCP-Session-Id']=sid;
      res.writeHead(upstream.status,responseHeaders); res.end(out); return;
    }
    json(res,404,{error:'not_found'});
  } catch (err) {
    const message = err?.message === 'request_too_large' ? 'request_too_large' : 'internal_error';
    json(res,message==='request_too_large'?413:500,{error:message});
  }
});

server.requestTimeout=150000;
server.headersTimeout=155000;
server.listen(PUBLIC_PORT,'0.0.0.0',()=>console.log(`Anthares OAuth MCP gateway listening on ${PUBLIC_PORT}`));
