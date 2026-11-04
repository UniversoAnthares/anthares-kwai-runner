// Anthares Remote notification-only protocol. No commands or database authority.
export const DEVICE_ID = 'DESKTOP-FTDK0HP';
export const WAKE_KIND = 'jobs_available';
const utf8 = new TextEncoder();
export function safeHexEquals(a,b) {
  if (!/^[a-f0-9]{64}$/i.test(String(a)) || !/^[a-f0-9]{64}$/i.test(String(b))) return false;
  let diff=0;
  for(let i=0;i<64;i++) diff|=a.charCodeAt(i)^b.charCodeAt(i);
  return diff===0;
}
export async function sha256hex(input,cryptoApi=globalThis.crypto) {
  const out=new Uint8Array(await cryptoApi.subtle.digest('SHA-256',utf8.encode(input)));
  return [...out].map(n=>n.toString(16).padStart(2,'0')).join('');
}
export async function validAgentToken(token,expectedHash,cryptoApi=globalThis.crypto) {
  if(typeof token!=='string'||token.length<20||token.length>1024||/[\r\n]/.test(token)) return false;
  return safeHexEquals(await sha256hex(token,cryptoApi),expectedHash);
}
export async function wakeMac(secret,timestamp,body,cryptoApi=globalThis.crypto) {
  if(typeof secret!=='string'||secret.length<32) throw Error('wake_secret_unconfigured');
  const key=await cryptoApi.subtle.importKey('raw',utf8.encode(secret),
    {name:'HMAC',hash:'SHA-256'},false,['sign']);
  const signed=utf8.encode(String(timestamp)+'\n'+String(body));
  const h=new Uint8Array(await cryptoApi.subtle.sign('HMAC',key,signed));
  return [...h].map(n=>n.toString(16).padStart(2,'0')).join('');
}
export async function verifyWakeNotification(request,secret,now=Date.now(),cryptoApi=globalThis.crypto) {
  if(typeof secret!=='string'||secret.length<32)return{ok:false,code:'not_configured'};
  const ts=request.headers.get('X-ARA-Wake-Timestamp')||'';
  const mac=request.headers.get('X-ARA-Wake-Signature')||'';
  if(!/^[0-9]{13}$/.test(ts)||!Number.isSafeInteger(Number(ts))||
     Math.abs(now-Number(ts))>30_000)return{ok:false,code:'invalid_timestamp'};
  if(!/^[a-f0-9]{64}$/i.test(mac))return{ok:false,code:'invalid_signature'};
  const raw=await request.text();
  if(utf8.encode(raw).length>256)return{ok:false,code:'oversized_body'};
  if(!safeHexEquals(mac,await wakeMac(secret,ts,raw,cryptoApi)))
    return{ok:false,code:'invalid_signature'};
  let event;try{event=JSON.parse(raw)}catch{return{ok:false,code:'invalid_body'}}
  if(!event||typeof event!=='object'||Array.isArray(event)||
     Object.keys(event).sort().join(',')!=='created_at_ms,device_id,kind,nonce'||
     event.kind!==WAKE_KIND||event.device_id!==DEVICE_ID||
     !Number.isSafeInteger(event.created_at_ms)||Math.abs(event.created_at_ms-Number(ts))>30_000||
     !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(event.nonce||''))
    return{ok:false,code:'invalid_event'};
  return{ok:true,code:'authorized_wake',device_id:DEVICE_ID};
}
export function makeWakeMessage(now=Date.now(),nonce=globalThis.crypto.randomUUID()) {
  return JSON.stringify({type:'wake',at_ms:now,nonce});
}
