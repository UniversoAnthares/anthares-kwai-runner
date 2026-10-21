const token=process.env.THREADS_ACCESS_TOKEN?.trim();
if(!token){console.error('THREADS_TOKEN_MISSING: configure repository Actions secret THREADS_ACCESS_TOKEN');process.exit(2);}
const controller=new AbortController(); const timeout=setTimeout(()=>controller.abort(),15000);
try{
 const r=await fetch('https://graph.threads.net/v1.0/me?fields=id,username',{headers:{Authorization:'Bearer '+token},signal:controller.signal});
 const d=await r.json();
 if(!r.ok||!d.id||d.username?.toLowerCase()!=='universoanthares'){console.error('THREADS_AUTH_GATE_FAILED',{http:r.status,error:d.error?.code||null,username_matches:d.username?.toLowerCase()==='universoanthares'});process.exitCode=3;}
 else console.log(JSON.stringify({ok:true,account:'universoanthares',account_id:d.id,api:'graph.threads.net',publish_executed:false}));
}catch(e){console.error('THREADS_AUTH_PROBE_FAILED',e.name);process.exitCode=4;}finally{clearTimeout(timeout);}
