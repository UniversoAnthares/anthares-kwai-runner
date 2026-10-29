// ARA Hostinger wake-only notification. Neon remains sole command authority.
export const WAKE_URL='https://anthares.us/ara-notify/index.php?action=signal';
export const WAKE_DEVICE='DESKTOP-FTDK0HP';
const TIMEOUT_MS=900;

export function prepareWake(device,secret){
  if(device!==WAKE_DEVICE)throw Error('wake_unknown_device');
  if(typeof secret!=='string'||!/^[A-Za-z0-9_-]{32,128}$/.test(secret))
    throw Error('wake_secret_missing');
  return {
    body:JSON.stringify({device_id:device}),
    headers:{
      'Content-Type':'application/json',
      'X-Anthares-Notify-Key':secret
    }
  };
}

// Send only after the canonical Neon INSERT/UPSERT resolves.
// A 202 receipt means that the broker recorded a wake, never job completion.
export async function notifyWakeAfterCommit(device,options={}){
  const env=options.env||process.env;
  if(env.ARA_WAKE_NOTIFY_ENABLED!=='1')
    return{enabled:false,ok:false,reason:'disabled'};
  const secret=env.ARA_WAKE_NOTIFY_SECRET;
  if(typeof secret!=='string'||!/^[A-Za-z0-9_-]{32,128}$/.test(secret))
    return{enabled:true,ok:false,reason:'unconfigured'};
  const fetchImpl=options.fetchImpl||globalThis.fetch;
  try{
    const payload=prepareWake(device,secret);
    const response=await fetchImpl(WAKE_URL,{
      method:'POST',headers:payload.headers,body:payload.body,
      signal:AbortSignal.timeout(TIMEOUT_MS),redirect:'error'
    });
    if(response.status!==202)
      return{enabled:true,ok:false,reason:'http_'+response.status};
    const receipt=await response.json();
    const seq=receipt?.sequence;
    if(receipt?.ok!==true||receipt?.protocol!=='ara-wake-v1'||
       !Number.isSafeInteger(seq)||seq<1)
      return{enabled:true,ok:false,reason:'bad_receipt'};
    return{enabled:true,ok:true,reason:'broker_recorded',sequence:seq};
  }catch(e){
    return{enabled:true,ok:false,reason:
      e?.name==='TimeoutError'||e?.name==='AbortError'?'timeout':'transport_unavailable'};
  }
}
