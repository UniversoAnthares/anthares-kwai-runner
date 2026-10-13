const DEFAULT_RENDER_FALLBACK = 'https://anthares-tiktok-render-rootless.onrender.com';

function cleanOrigin(value){
  return String(value||'').trim().replace(/\/$/,'');
}

async function forward(request, origin){
  const source=new URL(request.url);
  const target=new URL(source.pathname+source.search, origin+'/');
  const headers=new Headers(request.headers);
  headers.set('X-Anthares-Proxy','cloudflare-tiktok-router');
  const init={method:request.method,headers,redirect:'manual'};
  if(!['GET','HEAD'].includes(request.method)) init.body=request.body;
  return fetch(target,init);
}

export default {
  async fetch(request,env){
    const url=new URL(request.url);
    const primary=cleanOrigin(env.NORTHFLANK_TIKTOK_URL);
    const renderFallback=cleanOrigin(env.RENDER_TIKTOK_FALLBACK||DEFAULT_RENDER_FALLBACK);
    const allowRender=String(env.ALLOW_RENDER_FALLBACK||'0')==='1';

    if(url.pathname==='/router-health'){
      return Response.json({
        ok:!!primary,
        service:'anthares-tiktok-router',
        provider:'cloudflare',
        primary_provider:'northflank',
        primary_configured:!!primary,
        render_fallback_enabled:allowRender,
        render_required:false,
      },{status:primary?200:503});
    }
    if(!primary) return Response.json({ok:false,error:'northflank_upstream_not_configured'}, {status:503});

    try{
      const response=await forward(request,primary);
      // Never fail over state-changing requests automatically: publication may have
      // succeeded even if the response was lost. Render is an explicit emergency
      // fallback only for safe reads unless operators deliberately target it.
      if(response.status<500 || !allowRender || !['GET','HEAD'].includes(request.method)) return response;
    }catch(err){
      if(!allowRender || !['GET','HEAD'].includes(request.method)){
        return Response.json({ok:false,error:'northflank_unavailable',render_required:false},{status:503});
      }
    }
    return forward(request,renderFallback);
  }
};
