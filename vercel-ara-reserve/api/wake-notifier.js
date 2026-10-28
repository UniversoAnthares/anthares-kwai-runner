'use strict';
// Reserve ARA: Hostinger signal-only transport; Neon remains the only job queue.
// This module never transmits command args, job identifiers or credential values.
const SIGNAL_URL='https://anthares.us/ara-notify/index.php?action=signal';
const DEVICE='DESKTOP-FTDK0HP';
const MAX_MS=1250;
async function notifyWakeAfterCommit(device,{env=process.env,fetchImpl=globalThis.fetch}={}){
  if(env.ARA_WAKE_NOTIFY_ENABLED!=='1')
    return {enabled:false,ok:false,reason:'disabled'};
  if(device!==DEVICE)
    return {enabled:true,ok:false,reason:'other_device'};
  const secret=env.ARA_WAKE_NOTIFY_SECRET;
  if(typeof secret!=='string'||!/^[A-Za-z0-9_-]{32,128}$/.test(secret))
    return {enabled:true,ok:false,reason:'unconfigured'};
  try{
    const response=await fetchImpl(SIGNAL_URL,{
      method:'POST',
      headers:{'Content-Type':'application/json','X-Anthares-Notify-Key':secret},
      body:JSON.stringify({device_id:device}),
      signal:AbortSignal.timeout(MAX_MS),
      redirect:'error'
    });
    if(response.status!==202)
      return {enabled:true,ok:false,reason:'http_'+response.status};
    let receipt={};
    try{receipt=await response.json();}catch{}
    const sequence=Number(receipt?.sequence);
    if(Number.isSafeInteger(sequence)&&sequence>=1)
      return {enabled:true,ok:true,reason:'broker_recorded',sequence};
    return {enabled:true,ok:true,reason:'broker_accepted'};
  }catch(e){
    return {enabled:true,ok:false,
      reason:e?.name==='AbortError'||e?.name==='TimeoutError'?'timeout':'transport_error'};
  }
}
module.exports={notifyWakeAfterCommit,SIGNAL_URL,DEVICE};
