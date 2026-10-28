// Anthares Remote post-commit wake-only notifier.
// This transport never stores a job, changes a lease or creates a second queue.
// Deliberately OFF by default. The canonical Neon queue remains authoritative.
import crypto from 'node:crypto';

export const WAKE_URL='https://anthares-ara-wake.anthares1.workers.dev/notify';
export const WAKE_DEVICE='DESKTOP-FTDK0HP';
const SECRET_MIN=32;
const TIMEOUT_MS=900;

export function signedWake(device,secret,at=Date.now(),nonce=crypto.randomUUID()){
  if(device!==WAKE_DEVICE)throw Error('wake_unknown_device');
  if(typeof secret!=='string'||secret.length<SECRET_MIN)throw Error('wake_secret_missing');
  if(!Number.isSafeInteger(at)||at<0)throw Error('wake_timestamp_invalid');
  const body=JSON.stringify({
    device_id:device,kind:'jobs_available',created_at_ms:at,nonce
  });
  const signature=crypto.createHmac('sha256',secret)
    .update(String(at)+'\n'+body).digest('hex');
  return {
    body,
    headers:{
      'Content-Type':'application/json',
      'X-ARA-Wake-Timestamp':String(at),
      'X-ARA-Wake-Signature':signature
    }
  };
}

export async function notifyWakeAfterCommit(device,options={}){
  const env=options.env||process.env;
  if(env.ARA_WAKE_NOTIFY_ENABLED!=='1')
    return{enabled:false,ok:false,reason:'disabled'};
  if(typeof env.ARA_WAKE_NOTIFY_SECRET!=='string'||
     env.ARA_WAKE_NOTIFY_SECRET.length<SECRET_MIN)
    return{enabled:true,ok:false,reason:'unconfigured'};
  // Never accept an arbitrary target URL from the environment.
  // Fixed hostname/path prevent an SSRF or key leak from misconfiguration.
  const fetchImpl=options.fetchImpl||globalThis.fetch;
  try{
    const payload=signedWake(device,env.ARA_WAKE_NOTIFY_SECRET,
      options.now??Date.now(),options.nonce||crypto.randomUUID());
    const response=await fetchImpl(WAKE_URL,{
      method:'POST',
      headers:payload.headers,
      body:payload.body,
      signal:AbortSignal.timeout(TIMEOUT_MS),
      redirect:'error'
    });
    if(!response.ok)
      return{enabled:true,ok:false,reason:'http_'+response.status};
    const receipt=await response.json();
    // delivered=0 means there was no connected device, NOT a command failure.
    const delivered=Number(receipt?.delivered);
    return{enabled:true,ok:receipt?.ok===true&&Number.isInteger(delivered)&&delivered>0,
      delivered:Number.isInteger(delivered)&&delivered>=0?delivered:0,
      reason:receipt?.ok===true?'receipt':'bad_receipt'};
  }catch(e){
    // No job mutation or retries: the original 2-second poll remains active.
    return{enabled:true,ok:false,reason:
      e?.name==='TimeoutError'||e?.name==='AbortError'?'timeout':'transport_unavailable'};
  }
}
