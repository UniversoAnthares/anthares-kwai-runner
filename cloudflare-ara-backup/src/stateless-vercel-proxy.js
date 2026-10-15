const TARGET='https://anthares-ara-vercel-reserve.vercel.app';

export default {
  async fetch(request) {
    const incoming=new URL(request.url);
    const target=new URL(incoming.pathname+incoming.search,TARGET);
    const headers=new Headers(request.headers);
    headers.delete('host');
    headers.delete('cf-connecting-ip');
    headers.delete('cf-ipcountry');
    headers.delete('cf-ray');
    headers.delete('cf-visitor');
    headers.set('x-ara-proxy-origin','anthares-ara-backup');
    const init={method:request.method,headers,redirect:'manual'};
    if(request.method!=='GET'&&request.method!=='HEAD')init.body=request.body;
    const response=await fetch(target,init);
    const outHeaders=new Headers(response.headers);
    outHeaders.set('x-ara-transport','vercel-neon-stateless-proxy');
    outHeaders.set('cache-control','no-store');
    return new Response(response.body,{status:response.status,statusText:response.statusText,headers:outHeaders});
  }
};
