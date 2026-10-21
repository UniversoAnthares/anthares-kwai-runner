// Safe retry for failures that occurred strictly before pressing Post.
// Submitted/uncertain posts are excluded and require evidence reconciliation.
export function shouldAttemptPreSubmit(state,now=Date.now()){
 if(!state)return true;
 if(state.status!=='failed_pre_submit')return false;
 const attempts=Math.max(0,Number(state.attempts)||0);
 const retryAt=Date.parse(state.failed_at||state.claimedAt||'');
 if(!Number.isFinite(retryAt))return false;
 const backoff=Math.min(60*60_000,8*60_000*2**Math.min(3,Math.max(0,attempts-1)));
 return now-retryAt>=backoff;
}