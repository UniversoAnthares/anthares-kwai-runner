// Cloudflare edge route to the independent Neon Functions queue.
// Fixed upstream, no dynamic proxying, no authentication bypass, no media hosting.
const UPSTREAM='https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/';
const WRITE=new Set(['enqueue','buffer-lease','buffer-start','buffer-fail','buffer-scheduled',
 'buffer-pending','buffer-reconcile','buffer-stats','buffer-retention']);
export default {async fetch(request){
 const u=new URL(request.url),method=request.method,act=u.searchParams.get('action')||'';
 if(method==='GET'&&(u.pathname==='/healthz'||u.pathname==='/'||u.pathname==='/api/cortes-queue')){
   if(u.pathname==='/api/cortes-queue'&&act!=='health')
      return Response.json({ok:false,error:'NOT_FOUND'},{status:404});
   return relay(request,'health');
 }
 if(!['/','/api/cortes-queue'].includes(u.pathname)||method!=='POST'||!WRITE.has(act))
    return Response.json({ok:false,error:'NOT_FOUND'},{status:404});
 if(Number(request.headers.get('content-length')||0)>65536)
    return Response.json({ok:false,error:'TOO_LARGE'},{status:413});
 if(!/^Bearer [A-Za-z0-9_.-]{60,16000}$/.test(request.headers.get('authorization')||''))
    return Response.json({ok:false,error:'OIDC_REQUIRED'},{status:401});
 return relay(request,act);
}};
async function relay(request,action){
 try{
  const headers={'Accept':'application/json'};
  if(request.method==='POST'){
   headers['Content-Type']='application/json';
   headers['Authorization']=request.headers.get('authorization')||'';
  }
  const body=request.method==='POST'?await request.text():undefined;
  if(body&&body.length>65536)
    return Response.json({ok:false,error:'TOO_LARGE'},{status:413});
  const response=await fetch(UPSTREAM+'?action='+encodeURIComponent(action),{
    method:request.method,headers,body,
    redirect:'manual',signal:AbortSignal.timeout(22000)});
  if(response.status>=300&&response.status<400)
    return Response.json({ok:false,error:'UPSTREAM_REDIRECT_BLOCKED'},{status:503});
  return new Response(response.body,{status:response.status,
    headers:{'Content-Type':'application/json','Cache-Control':'no-store',
      'X-Anthares-Queue-Route':'cloudflare-neon'}});
 }catch{
  return Response.json({ok:false,error:'NEON_UPSTREAM_UNAVAILABLE'},{status:503});
 }
}
