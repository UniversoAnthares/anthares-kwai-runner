// Cloudflare independent ingress to Neon Functions: no Vercel calls, no secrets.
const BACKENDS=[
 "https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/",
 "https://br-crimson-unit-b89nau08-cortesbackup.compute.c-14.us-east-1.aws.neon.tech/"
];
const ACTIONS=new Set(["enqueue","buffer-lease","buffer-start","buffer-fail","buffer-scheduled","buffer-pending","buffer-reconcile"]);
function respond(code,error){return Response.json({ok:false,error},{status:code,headers:{"Cache-Control":"no-store"}});}
export default {async fetch(request){
 const url=new URL(request.url),action=url.searchParams.get("action")||"";
 const health=request.method==="GET"&&action==="health";
 if(!health&&!(request.method==="POST"&&ACTIONS.has(action)))return respond(404,"not_found");
 if(!health){
  const auth=request.headers.get("Authorization")||"";
  if(!auth.startsWith("Bearer ")||auth.length<68||auth.length>16007||!/^[A-Za-z0-9_.-]+$/.test(auth.slice(7)))return respond(401,"unauthorized");
  const ct=request.headers.get("Content-Type")||"";
  if(!ct.toLowerCase().includes("application/json"))return respond(415,"json_required");
  const len=Number(request.headers.get("Content-Length")||"0");
  if(len>131072)return respond(413,"body_too_large");
 }
 const payload=health?null:await request.text();
 if(payload&&payload.length>131072)return respond(413,"body_too_large");
 for(const upstream of BACKENDS){
  const target=upstream+"?action="+encodeURIComponent(action);
  const headers=new Headers({"Accept":"application/json"});
  if(!health){headers.set("Content-Type","application/json");headers.set("Authorization",request.headers.get("Authorization"));}
  try{
   const response=await fetch(target,{method:request.method,headers,body:payload||undefined,
      redirect:"manual",signal:AbortSignal.timeout(12000)});
   // Only infrastructure faults trigger failover; do not bypass rate limits or auth.
   if(response.status>=500)continue;
   const body=await response.text();
   const outputHeaders=new Headers({"Content-Type":"application/json","Cache-Control":"no-store",
      "X-Anthares-Queue-HA":"cloudflare-neon"});
   return new Response(body,{status:response.status,headers:outputHeaders});
  }catch{continue;}
 }
 return respond(503,"all_independent_backends_unavailable");
}};
