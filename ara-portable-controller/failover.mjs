/** ARA failover client: no Cloudflare, no Render.
 * Only returns candidates that have a valid fencing lease.
 * Never retries an operation across providers after dispatch without an idempotency key.
 */
export async function chooseController({origins,deviceId,token,timeoutMs=3500}){
 if(!Array.isArray(origins)||origins.length!==3||new Set(origins).size!==3)throw Error("exactly_three_distinct_origins_required");
 for(const origin of origins){
  const abort=new AbortController();const timer=setTimeout(()=>abort.abort(),timeoutMs);
  try{
   const url=new URL("/v1/device/auth-check",origin);
   if(url.protocol!=="https:")throw Error("https_required");
   const r=await fetch(url,{headers:{"Authorization":`Bearer ${token}`,"X-Anthares-Device":deviceId},signal:abort.signal,cache:"no-store"});
   if(!r.ok)continue;
   const x=await r.json();
   if(x.authenticated===true&&x.fence_owned===true&&/^\d+$/.test(String(x.epoch||"")))return {origin:url.origin,epoch:String(x.epoch)};
  }catch{}finally{clearTimeout(timer)}
 }
 return null; // fail closed: never select an unfenced controller
}
export async function controllerRead({origins,deviceId,token,path}){
 const selected=await chooseController({origins,deviceId,token});
 if(!selected)return {ok:false,error:"no_fenced_controller"};
 const u=new URL(path,selected.origin);
 const r=await fetch(u,{headers:{"Authorization":`Bearer ${token}`,"X-Anthares-Device":deviceId},cache:"no-store"});
 return {ok:r.ok,status:r.status,controller:selected.origin,epoch:selected.epoch,body:r.status===204?null:await r.json()};
}
