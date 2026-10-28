// Isolated wake-only Cloudflare Worker. No commands, storage, SQL or leases.
import { DurableObject } from 'cloudflare:workers';
import { DEVICE_ID, validAgentToken, verifyWakeNotification, makeWakeMessage } from './protocol.mjs';

const HASH_URL='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/devices/DESKTOP-FTDK0HP.sha256';
const JSON_HEADERS={'Content-Type':'application/json','Cache-Control':'no-store'};
const json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:JSON_HEADERS});
const stub=env=>env.ARA_WAKE_CHANNEL.get(env.ARA_WAKE_CHANNEL.idFromName(DEVICE_ID));

async function trustedHash() {
  const r=await fetch(HASH_URL,{redirect:'error',
    headers:{'User-Agent':'AntharesARA-Wake/1.0'},signal:AbortSignal.timeout(5000)});
  if(!r.ok)throw Error('trusted_hash_unavailable');
  const h=(await r.text()).trim().toLowerCase();
  if(!/^[a-f0-9]{64}$/.test(h))throw Error('trusted_hash_invalid');
  return h;
}

export class AraWakeChannel extends DurableObject {
  async fetch(request) {
    const route=new URL(request.url).pathname;
    if(route==='/internal/connect' && request.method==='GET' &&
        request.headers.get('Upgrade')?.toLowerCase()==='websocket') {
      if(this.ctx.getWebSockets().length>=3)return json({error:'connection_limit'},429);
      const pair=new WebSocketPair();
      const [client,server]=Object.values(pair);
      this.ctx.acceptWebSocket(server);
      server.serializeAttachment({device_id:DEVICE_ID,connected_at_ms:Date.now()});
      server.send(JSON.stringify({type:'ready',at_ms:Date.now()}));
      return new Response(null,{status:101,webSocket:client});
    }
    if(route==='/internal/notify' && request.method==='POST') {
      const wake=makeWakeMessage();
      let delivered=0;
      for(const socket of this.ctx.getWebSockets()) {
        if(socket.deserializeAttachment()?.device_id!==DEVICE_ID)continue;
        try{socket.send(wake);delivered++}catch{/* Existing HTTP queue is fallback. */}
      }
      return json({ok:true,delivered});
    }
    return json({error:'not_found'},404);
  }
  webSocketMessage(socket,message){if(message==='ping')socket.send('pong')}
  webSocketClose(socket,code,reason){try{socket.close(code,reason)}catch{}}
  webSocketError(socket){try{socket.close(1011,'wake_channel_error')}catch{}}
}

export default {
  async fetch(request,env) {
    const route=new URL(request.url).pathname;
    const ready=Boolean(env.ARA_WAKE_CHANNEL &&
      typeof env.ARA_WAKE_NOTIFY_SECRET==='string' &&
      env.ARA_WAKE_NOTIFY_SECRET.length>=32);
    if(route==='/health' && request.method==='GET')
      return json({ok:ready,role:'wake_only',database_writes:0,social_publication:false},
        ready?200:503);
    if(!ready)return json({error:'not_configured'},503);
    if(route==='/connect' && request.method==='GET') {
      if(request.headers.get('Upgrade')?.toLowerCase()!=='websocket')
        return json({error:'upgrade_required'},426);
      if(new URL(request.url).searchParams.get('device_id')!==DEVICE_ID)
        return json({error:'unknown_device'},404);
      const auth=request.headers.get('Authorization')||'';
      if(!/^Bearer [^\r\n]{20,1024}$/.test(auth))
        return json({error:'unauthorized'},401);
      let accepted=false;
      try{accepted=await validAgentToken(auth.slice(7),await trustedHash())}
      catch{return json({error:'trusted_auth_unavailable'},503)}
      if(!accepted)return json({error:'unauthorized'},401);
      return stub(env).fetch(new Request('https://internal/connect',
        {headers:{Upgrade:'websocket'}}));
    }
    if(route==='/notify' && request.method==='POST') {
      let proof;
      try{proof=await verifyWakeNotification(request,env.ARA_WAKE_NOTIFY_SECRET)}
      catch{return json({error:'verification_unavailable'},503)}
      if(!proof.ok)
        return json({error:proof.code},proof.code==='not_configured'?503:401);
      return stub(env).fetch(new Request('https://internal/notify',{method:'POST'}));
    }
    return json({error:'not_found'},404);
  }
};
