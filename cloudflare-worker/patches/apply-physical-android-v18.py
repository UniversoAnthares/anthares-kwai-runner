#!/usr/bin/env python3
"""Promote the proven Redmi/Kwai native HID executor without reviving retired PC/local routing.

Applied to the Cloudflare deploy snapshot after publisher-target v17. The new
executor is authenticated by a dedicated RSA public key; the private key never
leaves the authorized Anthares host. Requests are timestamped and signatures
are bound to HTTP method, path and exact request body.
"""
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"src"/"index.js"
s=p.read_text(encoding="utf-8-sig")
OLD='2026-10-15-publisher-target-v17'
NEW='2026-10-17-physical-android-v18'
OLD_ROUTING='2026-10-14-render-retired-r2'
NEW_ROUTING='2026-10-17-physical-android-r1'

if NEW in s:
    print('PHYSICAL_ANDROID_V18_ALREADY_APPLIED=1')
    raise SystemExit(0)
if OLD not in s:
    raise SystemExit('expected publisher-target v17 snapshot not found')

s=s.replace(f'CONTROL_VERSION="{OLD}"',f'CONTROL_VERSION="{NEW}"',1)
s=s.replace(f'ROUTING_REVISION="{OLD_ROUTING}"',f'ROUTING_REVISION="{NEW_ROUTING}"',1)

auth_anchor='''function retiredExecutor(id){return RETIRED_EXECUTORS.has(String(id||"").toLowerCase());}\nasync function executorAuth(request,env,body,rawBody=""){\n  const id=String(body.executor||"");\n  if(retiredExecutor(id)) return false;'''
auth_insert='''function retiredExecutor(id){return RETIRED_EXECUTORS.has(String(id||"").toLowerCase());}\nconst PHYSICAL_ANDROID_EXECUTOR="physical_android";\nconst PHYSICAL_ANDROID_PUBLIC_KEY=`-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwqMVKLsftqOwVa5U7CWq\nksPdck2z17p1sJMbFI8Ul7YeRaayxEI3l91NApPpSr5SjNZnTnZ/lmZiowXs6tdb\nVrPPcj8Ip5tiYcuuQlZ4ItBD0cfj0KuDpBiGyWJkKrtSz89GRHePP1eI6VsiBlhG\nQSUaxQ71RjAuCBB0miPcZ58iy+G4NzOP8p3PjgCq7nfVIQqJMDbORydzPjDIgLbW\nKibXLbbvIThyanJ0wgK4fr4ciUsn67ZGsWSEYpr8A303TMXjmDyvd3TFz+9mKEUh\nZYejXgb2k/0KgIUsSlXMkXe1E7lDfKoNWmKiu3z633hmu+KpTraHn1WTf2aiRPR/\ndQIDAQAB\n-----END PUBLIC KEY-----`;\nlet physicalAndroidVerifyKey=null;\nfunction b64Bytes(s){const raw=atob(String(s||"").replace(/\\s+/g,"")),out=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return out;}\nfunction publicSpkiBytes(pem){return b64Bytes(pem.replace(/-----BEGIN PUBLIC KEY-----|-----END PUBLIC KEY-----/g,"").replace(/\\s+/g,""));}\nasync function physicalAndroidAuth(request,rawBody){\n  try{\n    const ts=String(request.headers.get("X-Anthares-Executor-Timestamp")||"").trim();\n    const supplied=String(request.headers.get("X-Anthares-Executor-Signature")||"").trim();\n    const tsMs=Number(ts)*1000;\n    if(!ts||!supplied||!Number.isFinite(tsMs)||Math.abs(Date.now()-tsMs)>300000||typeof rawBody!=="string")return false;\n    if(!physicalAndroidVerifyKey)physicalAndroidVerifyKey=await crypto.subtle.importKey("spki",publicSpkiBytes(PHYSICAL_ANDROID_PUBLIC_KEY),{name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"},false,["verify"]);\n    const path=new URL(request.url).pathname;\n    const signed=ts+"\\n"+request.method.toUpperCase()+"\\n"+path+"\\n"+rawBody;\n    return await crypto.subtle.verify("RSASSA-PKCS1-v1_5",physicalAndroidVerifyKey,b64Bytes(supplied),new TextEncoder().encode(signed));\n  }catch{return false;}\n}\nasync function executorAuth(request,env,body,rawBody=""){\n  const id=String(body.executor||"");\n  if(id===PHYSICAL_ANDROID_EXECUTOR)return await physicalAndroidAuth(request,rawBody);\n  if(retiredExecutor(id)) return false;'''
if auth_anchor not in s:
    raise SystemExit('executor auth anchor missing')
s=s.replace(auth_anchor,auth_insert,1)

old_priority='function priorities(){return {cuts:["github"],tiktok:["github"],kwai:["github"],kwai_live:["hls_origin","github"],control:["cloudflare","github"]};}'
new_priority='function priorities(){return {cuts:["github"],tiktok:["github"],kwai:["physical_android","github"],kwai_live:["hls_origin","github"],control:["cloudflare","github"]};}'
if old_priority not in s:
    raise SystemExit('priority anchor missing')
s=s.replace(old_priority,new_priority,1)

base_anchor='''  {executor:"github",healthy:true,heartbeat_at:hb,ready_for_tiktok:true,tiktok_ready_until:until,capabilities:["cuts","tiktok","kwai","kwai_live","control"],daily_limit:100,published_today:0},\n  {executor:"hls_origin",healthy:true,heartbeat_at:hb,capabilities:["kwai_live"]},'''
base_new='''  {executor:"github",healthy:true,heartbeat_at:hb,ready_for_tiktok:true,tiktok_ready_until:until,capabilities:["cuts","tiktok","kwai","kwai_live","control"],daily_limit:100,published_today:0},\n  {executor:"physical_android",healthy:true,heartbeat_at:hb,capabilities:["kwai"],daily_limit:100,published_today:0},\n  {executor:"hls_origin",healthy:true,heartbeat_at:hb,capabilities:["kwai_live"]},'''
if base_anchor not in s:
    raise SystemExit('failover base anchor missing')
s=s.replace(base_anchor,base_new,1)

old_check='  kwai_github_only:selectHost("kwai",base)==="github",'
new_check='''  kwai_physical_primary:selectHost("kwai",base)==="physical_android",\n  kwai_github_failover:selectHost("kwai",withPatch({physical_android:{healthy:false}}))==="github",\n  kwai_physical_stale_failover:selectHost("kwai",withPatch({physical_android:{heartbeat_at:stale}}))==="github",'''
if old_check not in s:
    raise SystemExit('kwai failover check anchor missing')
s=s.replace(old_check,new_check,1)

heartbeat_old='''  if(url.pathname==="/heartbeat"&&request.method==="POST"){\n   const b=await request.json(); if(!b.executor)return json({ok:false,error:"executor_required"},400); if(retiredExecutor(b.executor))return json({ok:false,error:"retired_executor"},410); if(!(await executorAuth(request,env,b)))return json({ok:false,error:"unauthorized"},401);'''
heartbeat_new='''  if(url.pathname==="/heartbeat"&&request.method==="POST"){\n   const rawBody=await request.text(); let b; try{b=JSON.parse(rawBody);}catch{return json({ok:false,error:"invalid_json"},400);} if(!b.executor)return json({ok:false,error:"executor_required"},400); if(retiredExecutor(b.executor))return json({ok:false,error:"retired_executor"},410); if(!(await executorAuth(request,env,b,rawBody)))return json({ok:false,error:"unauthorized"},401);'''
if heartbeat_old not in s:
    raise SystemExit('heartbeat auth anchor missing')
s=s.replace(heartbeat_old,heartbeat_new,1)

assert 'const RETIRED_EXECUTORS=new Set(["local","pc","windows","oracle","google","google_compute"]);' in s
assert 'kwai:["physical_android","github"]' in s
assert 'id===PHYSICAL_ANDROID_EXECUTOR' in s
assert 'X-Anthares-Executor-Timestamp' in s
assert 'X-Anthares-Executor-Signature' in s
assert NEW in s and NEW_ROUTING in s

p.write_text(s,encoding='utf-8')
print('PHYSICAL_ANDROID_V18_APPLIED=1')
