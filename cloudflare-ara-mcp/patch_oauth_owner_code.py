#!/usr/bin/env python3
from pathlib import Path
import re

p = Path(__file__).with_name("src") / "index.js"
s = p.read_text(encoding="utf-8")

OWNER_HASH = "6Z-3WlmAvh6o7m_W0eYEpEo23YKZtjn-DLJpyjtEfQ0"

# Always rotate the configured hash; existing source may contain a stale hash.
needle = "const te=new TextEncoder();"
assignment = f"const OWNER_APPROVAL_HASH='{OWNER_HASH}';"
if re.search(r"const OWNER_APPROVAL_HASH='[^']*';", s):
    s = re.sub(r"const OWNER_APPROVAL_HASH='[^']*';", lambda _: assignment, s, count=1)
elif needle in s:
    s = s.replace(needle, assignment + "\\n" + needle, 1)
else:
    raise SystemExit("owner hash insertion target missing")

consume = "  async consume(kind,jti,exp){const key=`used:${kind}:${jti}`;if(await this.ctx.storage.get(key))return false;await this.ctx.storage.put(key,Number(exp)*1000);return true;}\n"
if "async pinnedClient()" not in s:
    if consume not in s:
        raise SystemExit("consume insertion target missing")
    s = s.replace(
        consume,
        consume
        + "  async pinnedClient(){return String((await this.ctx.storage.get('pinnedClient'))||'');}\n"
        + "  async pinClient(clientId){const current=await this.pinnedClient();if(current&&current!==clientId)return false;if(!current)await this.ctx.storage.put('pinnedClient',String(clientId));return true;}\n",
        1,
    )

helper_pattern = r"(?:\/\/ A successful queue\/command acknowledgement.*?\n)?async function sendApproval\(env,code\)\{.*?\n\}\nfunction rpcResult"
helper_repl = """async function clientAllowed(env,cid){if(!validClient(cid))return false;const pinned=await st(env).pinnedClient();return !pinned||pinned===cid;}\nasync function ownerCodeOk(value){return eq(await sha256b64(String(value||'')),OWNER_APPROVAL_HASH);}\nfunction rpcResult"""
s, n = re.subn(helper_pattern, helper_repl, s, count=1, flags=re.S)
if n != 1 and "async function ownerCodeOk" not in s:
    raise SystemExit(f"approval helper patch count={n}")

health_pattern = r" if\(req\.method==='GET'&&\(u\.pathname==='/'\|\|u\.pathname==='/health'\)\)\{.*?\n if\(req\.method==='GET'&&u\.pathname==='\/\.well-known\/ara-control-key'\)"
health_repl = """ if(req.method==='GET'&&(u.pathname==='/'||u.pathname==='/health')){await st(env).ensure();let controlReady=false,connected=false;try{const s=await status(env,DEFAULT_DEVICE);controlReady=true;connected=!!s.connected;}catch{}const pinned=!!(await st(env).pinnedClient());return json({ok:controlReady,service:'anthares-ara-mcp',provider:'cloudflare',render_independent:true,control:CONTROL,control_ready:controlReady,device_connected:connected,oauth:true,mcp:true,oauth_owner_code_mode:'chat_setup_code',oauth_client_pinned:pinned},controlReady?200:503);}\n if(req.method==='GET'&&u.pathname==='/.well-known/ara-control-key')"""
s, n = re.subn(health_pattern, health_repl, s, count=1, flags=re.S)
if n != 1 and "oauth_owner_code_mode:'chat_setup_code'" not in s:
    raise SystemExit(f"health patch count={n}")

get_pattern = r" if\(req\.method==='GET'&&u\.pathname==='/oauth/authorize'\)\{.*?\n if\(req\.method==='POST'&&u\.pathname==='/oauth/authorize'\)"
get_repl = """ if(req.method==='GET'&&u.pathname==='/oauth/authorize'){const cid=u.searchParams.get('client_id')||'',red=u.searchParams.get('redirect_uri')||'',challenge=u.searchParams.get('code_challenge')||'',method=u.searchParams.get('code_challenge_method')||'',resource=u.searchParams.get('resource')||ORIGIN,scopes=parseScopes(u.searchParams.get('scope'));if(!(await clientAllowed(env,cid))||!validRedirect(red)||u.searchParams.get('response_type')!=='code'||method!=='S256'||challenge.length<43||resource!==ORIGIN||!scopes)return json({error:'invalid_request'},400);const tx=await st(env).signToken({typ:'oauth_pending',iss:ORIGIN,aud:ORIGIN,exp:Math.floor(Date.now()/1000)+600,jti:rand(16),clientId:cid,redirectUri:red,challenge,scopes,scp:scopes,state:u.searchParams.get('state')||''});return html(`<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>Anthares Remote</title></head><body><main><h1>Anthares Remote</h1><p>Digite o código de configuração enviado ao e-mail cadastrado. Esta autorização não depende da área de transferência nem da sessão interativa do Windows.</p><form method=\"post\" action=\"/oauth/authorize\"><input type=\"hidden\" name=\"tx\" value=\"${esc(tx)}\"><label>Código <input type=\"password\" name=\"approval\" autocomplete=\"one-time-code\" required autofocus></label><button type=\"submit\">Autorizar</button></form></main></body></html>`);}\n if(req.method==='POST'&&u.pathname==='/oauth/authorize')"""
s, n = re.subn(get_pattern, get_repl, s, count=1, flags=re.S)
if n != 1 and "código de configuração enviado ao e-mail cadastrado" not in s:
    raise SystemExit(f"authorize GET patch count={n}")

post_pattern = r" if\(req\.method==='POST'&&u\.pathname==='/oauth/authorize'\)\{.*?\n if\(req\.method==='POST'&&u\.pathname==='/oauth/token'\)"
post_repl = """ if(req.method==='POST'&&u.pathname==='/oauth/authorize'){const f=await req.formData();const p=await st(env).verifyToken(f.get('tx')||'','oauth_pending');if(!p)return json({error:'authorization_expired'},400);if(!(await clientAllowed(env,p.clientId)))return json({error:'invalid_client'},400);if(!(await ownerCodeOk(f.get('approval')||'')))return json({error:'authorization_denied'},403);if(!(await st(env).consume('oauth_pending',p.jti,p.exp)))return json({error:'authorization_replayed'},400);if(!(await st(env).pinClient(p.clientId)))return json({error:'invalid_client'},400);const code=await st(env).signToken({typ:'oauth_code',iss:ORIGIN,aud:ORIGIN,exp:Math.floor(Date.now()/1000)+300,jti:rand(16),clientId:p.clientId,redirectUri:p.redirectUri,challenge:p.challenge,scopes:p.scopes,scp:p.scopes});const target=new URL(p.redirectUri);target.searchParams.set('code',code);if(p.state)target.searchParams.set('state',p.state);target.searchParams.set('iss',ORIGIN);return Response.redirect(target.toString(),302);}\n if(req.method==='POST'&&u.pathname==='/oauth/token')"""
s, n = re.subn(post_pattern, post_repl, s, count=1, flags=re.S)
if n != 1 and "authorization_replayed" not in s:
    raise SystemExit(f"authorize POST patch count={n}")

s = s.replace("if(!validClient(cid))return json({error:'invalid_client'},400);", "if(!(await clientAllowed(env,cid)))return json({error:'invalid_client'},400);", 1)
s = s.replace("serverInfo:{name:'Anthares Remote',version:'1.0.0'}", "serverInfo:{name:'Anthares Remote',version:'1.0.1'}", 1)

required = [
    "OWNER_APPROVAL_HASH=",
    "async pinnedClient()",
    "async function ownerCodeOk",
    "oauth_owner_code_mode:'chat_setup_code'",
    "authorization_replayed",
    "await clientAllowed(env,cid)",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing marker: {marker}")

p.write_text(s, encoding="utf-8")
print("OAUTH_OWNER_CODE_PATCH_OK=1")
