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

    if(url.pathname==='/router-health'){
      return Response.json({
        ok:!!primary,
        service:'anthares-tiktok-router',
        provider:'cloudflare',
        primary_provider:'northflank',
        primary_configured:!!primary,
        render_fallback_enabled:false,
        render_required:false,
      },{status:primary?200:503});
    }
    if(!primary) return Response.json({ok:false,error:'northflank_upstream_not_configured',render_required:false},{status:503});

    try{
      return await forward(request,primary);
    }catch(err){
      return Response.json({ok:false,error:'northflank_unavailable',render_required:false},{status:503});
    }
  }
};
