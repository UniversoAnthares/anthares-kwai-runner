#!/usr/bin/env python3
from pathlib import Path

p=Path(__file__).with_name('api')/'router.mjs'
s=p.read_text(encoding='utf-8')

anchor="async function deviceAuth(req){const device=String(req.headers['x-anthares-device']||'').trim();if(!/^[A-Za-z0-9_.-]{1,200}$/.test(device))return{ok:false,device:''};const token=bearer(req);if(!token)return{ok:false,device};const expected=await expectedDeviceHash(device);return{ok:!!expected&&safeEq(sha256hex(token),expected),device};}\n"
helper=r'''async function mcpControlKey(){const r=await fetch('https://anthares-ara-mcp.anthares1.workers.dev/.well-known/ara-control-key',{headers:{'User-Agent':'AntharesARAVercel/1.0','cache-control':'no-cache'}});if(!r.ok)throw new Error('mcp_control_key_unavailable');const pem=await r.text();if(!pem.includes('BEGIN PUBLIC KEY')||pem.length>4096)throw new Error('mcp_control_key_invalid');return pem;}
function controlTarget(req,route){const u=new URL(req.url,ORIGIN);const pairs=[];for(const[k,v]of u.searchParams.entries())if(k!=='route')pairs.push([k,v]);const qs=new URLSearchParams(pairs).toString();return `/${route}${qs?'?'+qs:''}`;}
async function verifyMcpControl(req,route){if(String(req.headers['x-ara-signer']||'')!=='anthares-remote-mcp')return false;const ts=String(req.headers['x-ara-timestamp']||''),sig=String(req.headers['x-ara-signature']||'');const n=Number(ts);if(!Number.isFinite(n)||Math.abs(Date.now()-n)>30000||!sig)return false;const raw=req.body===undefined||req.body===null?'':(typeof req.body==='string'?req.body:JSON.stringify(req.body));const payload=Buffer.from(`${ts}\n${String(req.method||'GET').toUpperCase()}\n${controlTarget(req,route)}\n${raw}`);let pem;try{pem=await mcpControlKey();if(!crypto.verify(null,payload,pem,Buffer.from(sig,'base64url')))return false;}catch{return false;}return consume('mcp_signature',sig,Math.floor(Date.now()/1000)+60);}
'''
if 'async function verifyMcpControl(' not in s:
    if anchor not in s: raise SystemExit('deviceAuth anchor missing')
    s=s.replace(anchor,anchor+helper,1)

route_anchor="if(route==='v1/device/auth-check'&&req.method==='GET'){"
routes=r'''if(route==='v1/mcp/status'&&req.method==='GET'){if(!(await verifyMcpControl(req,route)))return reply(res,401,{error:'unauthorized'});const device=String(req.query?.device_id||DEFAULT_DEVICE);return reply(res,200,await status(device));}
if(route==='v1/mcp/execute'&&req.method==='POST'){if(!(await verifyMcpControl(req,route)))return reply(res,401,{error:'unauthorized'});const b=jsonBody(req),device=String(b.device_id||DEFAULT_DEVICE),type=String(b.type||''),args=b.args&&typeof b.args==='object'?b.args:{},timeout=Math.max(1,Math.min(Number(b.timeout_seconds||30),100));if(!type)return reply(res,400,{error:'missing_type'});return reply(res,200,await execute(type,args,timeout,device));}
if(route==='v1/mcp/oauth/consume'&&req.method==='POST'){if(!(await verifyMcpControl(req,route)))return reply(res,401,{error:'unauthorized'});const b=jsonBody(req),kind=String(b.kind||''),issuer=String(b.issuer||''),jti=String(b.jti||''),exp=Number(b.exp||0);if(!kind||!issuer||!jti||!Number.isFinite(exp)||exp<=Math.floor(Date.now()/1000))return reply(res,400,{error:'invalid_replay_record'});await ensureSchema();const q=await pool.query(`INSERT INTO ara_oauth_consumed(kind,issuer,jti,expires_at) VALUES($1,$2,$3,to_timestamp($4)) ON CONFLICT DO NOTHING RETURNING jti`,[kind,issuer,jti,exp]);return reply(res,q.rowCount===1?200:409,{ok:q.rowCount===1,duplicate:q.rowCount!==1});}
'''
if "route==='v1/mcp/status'" not in s:
    if route_anchor not in s: raise SystemExit('route anchor missing')
    s=s.replace(route_anchor,routes+route_anchor,1)

for m in ['async function verifyMcpControl(',"route==='v1/mcp/status'","route==='v1/mcp/execute'","route==='v1/mcp/oauth/consume'",'mcp_signature']:
    if m not in s: raise SystemExit('missing '+m)

p.write_text(s,encoding='utf-8')
print('ARA_VERCEL_CONTROL_BRIDGE_PATCH_OK=1')
