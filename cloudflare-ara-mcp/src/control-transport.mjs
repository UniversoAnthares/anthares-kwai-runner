
const quotaUntil = new Map();
export async function requestControl({origins,path,method="GET",body,timeoutMs=15000,sign,fetchImpl=fetch,now=Date.now}) {
  const raw=body===undefined?"":JSON.stringify(body);
  const safelyRepeatable=method==="GET" || path==="/v1/mcp/oauth/consume";
  let lastError=new Error("control_unavailable");
  for (const origin of origins) {
    if ((quotaUntil.get(origin)||0)>now()) continue;
    const sig=await sign(method,path,raw);
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),Math.max(1,Math.min(timeoutMs,15000)));
    try {
      const r=await fetchImpl(origin+path,{method,headers:{"content-type":"application/json","x-ara-timestamp":sig.timestamp,"x-ara-signature":sig.signature,"x-ara-signer":"anthares-remote-mcp"},body:body===undefined?undefined:raw,signal:controller.signal,redirect:"manual"});
      // A Vercel quota rejection happens before application execution.
      const quota=r.status===429 || (r.status===402 && r.headers.get("x-vercel-error")==="DEPLOYMENT_DISABLED");
      if (quota) quotaUntil.set(origin,now()+300000);
      const retry=quota || (safelyRepeatable && (r.status===404 || r.status>=500));
      if (!retry) return r;
      lastError=new Error("control_http_"+r.status);
      await r.body?.cancel();
    } catch(e) {
      lastError=e;
      if (!safelyRepeatable) throw new Error("RECONCILE_REQUIRED");
    } finally {clearTimeout(timer);}
  }
  throw lastError;
}
