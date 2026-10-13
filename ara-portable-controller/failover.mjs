/** ARA automatic failover client: exactly three fenced controllers.
 * No Cloudflare. No Render. Shared state lives in Neon PostgreSQL.
 */
export const DEFAULT_ORIGINS=[
 "https://anthares-ara-vercel-reserve.vercel.app",
 "https://anthares-ara-controller-b.vercel.app",
 "https://anthares-ara-controller-c.vercel.app"
];
const headers=(deviceId,token,epoch)=>({"Authorization":`Bearer ${token}`,"X-Anthares-Device":deviceId,...(epoch?{"X-Anthares-Fence-Epoch":String(epoch)}:{})});
async function request(origin,path,{deviceId,token,epoch,method='GET',body,timeoutMs=3500}={}){
 const url=new URL(path,origin);if(url.protocol!=="https:")throw Error("https_required");
 const abort=new AbortController();const timer=setTimeout(()=>abort.abort(),timeoutMs);
 try{return await fetch(url,{method,headers:{...headers(deviceId,token,epoch),...(body?{"content-type":"application/json"}:{})},body:body?JSON.stringify(body):undefined,signal:abort.signal,cache:"no-store"})}finally{clearTimeout(timer)}
}
export async function chooseController({origins=DEFAULT_ORIGINS,deviceId,token,timeoutMs=3500,allowAcquire=true}){
 if(!Array.isArray(origins)||origins.length!==3||new Set(origins).size!==3)throw Error("exactly_three_distinct_origins_required");
 for(const origin of origins){
  try{const r=await request(origin,"/v1/device/auth-check",{deviceId,token,timeoutMs});if(!r.ok)continue;const x=await r.json();if(x.authenticated===true&&x.fence_owned===true&&/^\d+$/.test(String(x.epoch||"")))return {origin:new URL(origin).origin,epoch:String(x.epoch),acquired:false}}catch{}
 }
 if(!allowAcquire)return null;
 for(const origin of origins){
  try{const r=await request(origin,"/v1/device/fence/acquire",{deviceId,token,method:'POST',timeoutMs});if(!r.ok)continue;const x=await r.json();if(x.ok===true&&(x.fence_owned===true||x.acquired===true)&&/^\d+$/.test(String(x.epoch||"")))return {origin:new URL(origin).origin,epoch:String(x.epoch),acquired:true}}catch{}
 }
 return null;
}
export async function controllerRead({origins=DEFAULT_ORIGINS,deviceId,token,path}){
 const selected=await chooseController({origins,deviceId,token});
 if(!selected)return {ok:false,error:"no_fenced_controller"};
 const r=await request(selected.origin,path,{deviceId,token,epoch:selected.epoch});
 return {ok:r.ok,status:r.status,controller:selected.origin,epoch:selected.epoch,body:r.status===204?null:await r.json()};
}
export async function controllerWrite({origins=DEFAULT_ORIGINS,deviceId,token,path,body}){
 const selected=await chooseController({origins,deviceId,token});
 if(!selected)return {ok:false,error:"no_fenced_controller"};
 const r=await request(selected.origin,path,{deviceId,token,epoch:selected.epoch,method:'POST',body});
 return {ok:r.ok,status:r.status,controller:selected.origin,epoch:selected.epoch,body:r.status===204?null:await r.json()};
}
