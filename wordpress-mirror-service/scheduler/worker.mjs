function authorized(request,env){const value=request.headers.get('Authorization')||'';const secret=env.CRON_SECRET||'';if(secret.length<32||value.length!==secret.length+7)return false;let diff=0;const expected='Bearer '+secret;for(let i=0;i<expected.length;i++)diff|=expected.charCodeAt(i)^value.charCodeAt(i);return diff===0;}
async function invoke(env,ref,scheduledTime){
 const response=await fetch('https://anthares-wordpress-mirror.vercel.app/api/sync',{method:'POST',headers:{Authorization:'Bearer '+env.CRON_SECRET,'Content-Type':'application/json','x-mirror-trigger':'cloudflare-cron','x-mirror-scheduled-time':new Date(scheduledTime).toISOString()},body:JSON.stringify({ref}),signal:AbortSignal.timeout(285000)});
 let result;try{result=await response.json();}catch{result={ok:false,error:'EXECUTOR_INVALID_RESPONSE'};}
 return{http_status:response.status,...result};
}
export default{
 async fetch(request,env){
  const url=new URL(request.url);
  if(url.pathname==='/health')return Response.json({service:'anthares-wordpress-mirror-scheduler',executor:'vercel',state:'gitlab-atomic-ref-lock',ci_minutes_required:false,windows_required:false});
  if(!authorized(request,env))return Response.json({error:'unauthorized'},{status:401});
  if(url.pathname==='/status')return Response.json(await env.MIRROR_STATUS.get('latest','json')||{state:'never_scheduled'});
  return Response.json({error:'not_found'},{status:404});
 },
 async scheduled(controller,env,ctx){
  const started=new Date().toISOString();const results=[];
  try{
   results.push(await invoke(env,'main',controller.scheduledTime));
   if(env.VALIDATION_REF)results.push(await invoke(env,env.VALIDATION_REF,controller.scheduledTime));
  }catch{results.push({ok:false,error:'EXECUTOR_UNREACHABLE'});}
  const record={trigger:'cloudflare-native-cron',cron:controller.cron,scheduled_time:new Date(controller.scheduledTime).toISOString(),started_at:started,finished_at:new Date().toISOString(),ok:results.every(r=>r.ok),results};
  await env.MIRROR_STATUS.put('latest',JSON.stringify(record));
  await env.MIRROR_STATUS.put('run:'+controller.scheduledTime,JSON.stringify(record),{expirationTtl:604800});
  console.log(JSON.stringify({service:'wordpress-mirror-scheduler',scheduled_time:record.scheduled_time,ok:record.ok,run_ids:results.map(r=>r.run_id)}));
 }
};
