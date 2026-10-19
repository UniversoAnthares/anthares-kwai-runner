// Workers does not implement redirect:error. Never forward credentials across a redirect.
export async function fetchWithoutRedirects(url, init={}) {
  const response=await fetch(url,{...init,redirect:'manual'});
  if(response.status>=300 && response.status<400)throw new Error('upstream_redirect_rejected');
  return response;
}
