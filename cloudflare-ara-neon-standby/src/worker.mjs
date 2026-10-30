import {createHandler} from "./control.generated.mjs";
const handlers=new WeakMap();
export default {async fetch(request,env){
 const u=new URL(request.url);
 const headers={"cache-control":"no-store","x-content-type-options":"nosniff","x-ara-compute":"cloudflare-neon-standby"};
 if(!env.DATABASE_URL)return Response.json({ok:false,error:"standby_not_provisioned"},{status:503,headers});
 // No second OAuth issuer or anonymous command surface.
 if(u.pathname!=="/health" && !u.pathname.startsWith("/v1/"))return Response.json({error:"not_found"},{status:404,headers});
 if(u.pathname==="/health"){
  try{const {query}=await import("./database.mjs");const r=await query(env,"SELECT to_regclass('public.ara_oauth_consumed')::text AS replay,to_regclass('public.ara_reserve_jobs')::text AS jobs",[]);const ok=!!r.rows[0]?.replay&&!!r.rows[0]?.jobs;return Response.json({ok,provider:"cloudflare",state:"shared-neon",vercel_preserved:true},{status:ok?200:503,headers});}
  catch{return Response.json({ok:false,error:"standby_database_unavailable"},{status:503,headers});}
 }
 let handler=handlers.get(env);if(!handler){handler=createHandler(env);handlers.set(env,handler);}
 const req={method:request.method,url:request.url,headers:Object.fromEntries(request.headers),query:{...Object.fromEntries(u.searchParams),route:u.pathname.slice(1)}};
 if(!["GET","HEAD"].includes(request.method)){const raw=await request.text();if(raw.length>1048576)return new Response(null,{status:413});req.body=raw;}
 let status=200;const out=new Headers(headers);let response;
 const res={get statusCode(){return status},set statusCode(v){status=v},setHeader(k,v){out.set(k,v)},end(body){response=new Response(status===204?null:body,{status,headers:out})}};
 try{await handler(req,res);return response||Response.json({error:"empty_response"},{status:500,headers});}
 catch{return Response.json({error:"standby_internal_error"},{status:503,headers});}
}};
