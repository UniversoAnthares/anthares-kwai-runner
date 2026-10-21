// Independent TikTok queue ingress. No Vercel calls or credential storage.
// The upstream Neon Function authenticates signed GitHub OIDC claims.
const UPSTREAM='https://br-crimson-unit-b89nau08-cortestiktok.compute.c-14.us-east-1.aws.neon.tech/';
const ACTIONS=new Set(['enqueue','claim','start','confirm','fail']);
const failure=(status,error)=>Response.json({ok:false,error},{status,headers:{'Cache-Control':'no-store'}});
export default {async fetch(request){
 const u=new URL(request.url),action=u.searchParams.get('action')||'';
 if(request.method==='GET'&&!['health','status'].includes(action))return failure(404,'not_found');
 if(request.method==='POST'&&!ACTIONS.has(action))return failure(404,'not_found');
 if(!['/','/api/cortes-tiktok'].includes(u.pathname))return failure(404,'not_found');
 const auth=request.headers.get('authorization')||'';
 if(!(request.method==='GET'&&action==='health')&&!/^Bearer [A-Za-z0-9_.-]{200,16000}$/.test(auth))
   return failure(401,'oidc_required');
 let body;
 if(request.method==='POST'){
   if(!(request.headers.get('content-type')||'').toLowerCase().includes('application/json'))
     return failure(415,'json_required');
   body=await request.text();
   if(body.length>131072)return failure(413,'body_too_large');
 }
 try{
   const r=await fetch(UPSTREAM+'?action='+encodeURIComponent(action),{
     method:request.method,redirect:'manual',
     headers:{'Accept':'application/json',
       ...(request.method==='POST'?{'Content-Type':'application/json'}:{}),
       ...(auth?{'Authorization':auth}:{})},
     body,signal:AbortSignal.timeout(16000)});
   if(r.status>=300&&r.status<400)return failure(503,'unexpected_redirect');
   return new Response(r.body,{status:r.status,headers:{
     'Content-Type':'application/json','Cache-Control':'no-store',
     'X-Anthares-TikTok-Route':'cloudflare-neon'}});
 }catch{return failure(503,'neon_tiktok_unavailable');}
}};