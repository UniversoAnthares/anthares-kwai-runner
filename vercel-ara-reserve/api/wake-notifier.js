'use strict';
const https=require('node:https');
// Reserve ARA: Hostinger signal-only transport; Neon remains the only job queue.
// This module never transmits command args, job identifiers or credential values.
const SIGNAL_URL='https://anthares.us/ara-notify/index.php?action=signal';
const DEVICE='DESKTOP-FTDK0HP';
const MAX_MS=1250;

// HTTPS direct-to-origin for this single private webhook. Like curl --resolve:
// URL, Host header, SNI, certificate checks and bearer auth remain anthares.us.
function validPublicIPv4(value){
  if(typeof value!=='string')return false;
  const n=value.split('.').map(Number);
  return n.length===4&&n.every((x,i)=>Number.isInteger(x)&&x>=0&&x<=255&&
    String(x)===value.split('.')[i])&&n[0]!==0&&n[0]!==10&&n[0]!==127&&
    n[0]!==169&&n[0]<224&&!(n[0]===100&&n[1]>=64&&n[1]<=127)&&
    !(n[0]===172&&n[1]>=16&&n[1]<=31)&&!(n[0]===192&&n[1]===168);
}
function postDirectOrigin(device,secret,ip,requestImpl=https.request){
  return new Promise(resolve=>{
    let settled=false;
    const finish=result=>{if(!settled){settled=true;resolve(result);}};
    const body=JSON.stringify({device_id:device});
    const options={
      method:'POST',timeout:MAX_MS,agent:false,
      headers:{
        'Content-Type':'application/json',
        'Accept':'application/json',
        'Authorization':'Bearer '+secret,
        'User-Agent':'AntharesARA-Wake/1.0',
        'Content-Length':Buffer.byteLength(body)
      },
      lookup:(hostname,opts,callback)=>{
        if(hostname!=='anthares.us')return callback(new Error('wake_host_mismatch'));
        if(opts&&opts.all)return callback(null,[{address:ip,family:4}]);
        return callback(null,ip,4);
      }
    };
    try{
      const req=requestImpl(SIGNAL_URL,options,res=>{
        let responseBody='';
        res.on('data',chunk=>{
          responseBody+=chunk.toString();
          if(responseBody.length>2048)req.destroy(new Error('wake_response_oversized'));
        });
        res.on('error',()=>finish({enabled:true,ok:false,reason:'transport_error'}));
        res.on('end',()=>{
          if(res.statusCode!==202)
            return finish({enabled:true,ok:false,reason:'http_'+res.statusCode});
          let receipt={};
          try{receipt=JSON.parse(responseBody);}catch{}
          const sequence=Number(receipt?.sequence);
          if(Number.isSafeInteger(sequence)&&sequence>=1)
            return finish({enabled:true,ok:true,reason:'broker_recorded',sequence});
          return finish({enabled:true,ok:true,reason:'broker_accepted'});
        });
      });
      req.on('timeout',()=>req.destroy(Object.assign(new Error('wake_timeout'),{code:'WAKE_TIMEOUT'})));
      req.on('error',e=>finish({enabled:true,ok:false,
        reason:e?.code==='WAKE_TIMEOUT'?'timeout':'transport_error'}));
      req.end(body);
    }catch{finish({enabled:true,ok:false,reason:'transport_error'});}
  });
}

async function notifyWakeAfterCommit(device,{env=process.env,fetchImpl=globalThis.fetch,requestImpl=https.request}={}){
  if(env.ARA_WAKE_NOTIFY_ENABLED!=='1')
    return {enabled:false,ok:false,reason:'disabled'};
  if(device!==DEVICE)
    return {enabled:true,ok:false,reason:'other_device'};
  const secret=env.ARA_WAKE_NOTIFY_SECRET;
  if(typeof secret!=='string'||!/^[A-Za-z0-9_-]{32,128}$/.test(secret))
    return {enabled:true,ok:false,reason:'unconfigured'};
  if(env.ARA_WAKE_ORIGIN_IP){
    if(!validPublicIPv4(env.ARA_WAKE_ORIGIN_IP))
      return {enabled:true,ok:false,reason:'invalid_origin'};
    return await postDirectOrigin(device,secret,env.ARA_WAKE_ORIGIN_IP,requestImpl);
  }
  try{
    const response=await fetchImpl(SIGNAL_URL,{
      method:'POST',
      headers:{'Content-Type':'application/json','Accept':'application/json',
        'Authorization':'Bearer '+secret,
        'User-Agent':'Mozilla/5.0 (compatible; AntharesARA-Wake/1.0; +https://anthares.us)'},
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
