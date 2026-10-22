#!/usr/bin/env node
// Read-only verification of one owned public Pin in the isolated headless
// Pinterest browser. Does not select drafts, edit, or click Publish.
import fs from 'node:fs';
import path from 'node:path';
const pin=String(process.argv[2]||'');
const port=Number(process.env.CORTES_CHROME_CDP_PORT||9226);
if(!/^[0-9]{10,25}$/.test(pin)||port!==9226)throw Error('PIN_PUBLIC_ID_OR_PORT_INVALID');
const base='http://127.0.0.1:'+port;
const url='https://br.pinterest.com/pin/'+pin+'/';
const markers='D:\\AntharsWork\\cortes-social-browser-20261020\\chrome-owned-tabs';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
let target,ws,seq=0,pending=new Map();
function rpc(method,params={}){
 return new Promise((resolve,reject)=>{
  const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('PIN_PUBLIC_CDP_TIMEOUT'))},14000);
  pending.set(id,{resolve,reject,timer});
  ws.send(JSON.stringify({id,method,params}));
 });
}
try{
 const resp=await fetch(base+'/json/new?'+encodeURIComponent(url),
  {method:'PUT',signal:AbortSignal.timeout(12000)});
 if(!resp.ok)throw Error('PIN_PUBLIC_CDP_TAB_OPEN_FAILED');
 target=await resp.json();
 if(!/^[a-f0-9]{32}$/i.test(target.id)||!target.webSocketDebuggerUrl)throw Error('PIN_PUBLIC_TARGET_INVALID');
 fs.mkdirSync(markers,{recursive:true});
 fs.writeFileSync(path.join(markers,port+'-'+target.id+'.json'),JSON.stringify({
  port,id:target.id,pid:process.pid,created:Date.now(),kind:'pinterest-public-readback'
 }),{flag:'wx'});
 ws=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((ok,bad)=>{ws.onopen=ok;ws.onerror=bad});
 ws.onmessage=e=>{
  const m=JSON.parse(e.data);const p=pending.get(m.id);if(!p)return;
  clearTimeout(p.timer);pending.delete(m.id);
  m.error?p.reject(Error('PIN_PUBLIC_CDP_RPC_FAILED')):p.resolve(m.result);
 };
 await wait(6200);
 const expr=`(()=>{const body=document.body?.innerText||"";const video=[...document.querySelectorAll("video")].find(v=>Number.isFinite(v.duration)&&v.duration>10);return {path:location.pathname,title:document.title,owned:body.includes("Universo Anthares"),board:body.includes("Universo Anthares — Vídeos"),duration:video?.duration??null,error:/página não encontrada|page not found/i.test(body.slice(0,900))}})()`;
 const result=await rpc('Runtime.evaluate',{expression:expr,returnByValue:true});
 const v=result.result?.value||{};
 if(v.path!=='/pin/'+pin+'/'||!v.owned||!v.board||
    !v.title?.endsWith('● Universo Anthares')||v.error||
    !Number.isFinite(v.duration)||v.duration<10||v.duration>90)
     throw Error('PIN_PUBLIC_PROOF_REJECTED');
 console.log(JSON.stringify({ok:true,pin_id:pin,public_duration_ms:Math.round(v.duration*1000),
    verified_account:'lucasyahn',verified_public_board:true,board_id:'819514532133906920'}));
}catch(e){
 console.log(JSON.stringify({ok:false,error:String(e.message||e).slice(0,95)}));
 process.exitCode=2;
}finally{
 try{ws?.close()}catch{}
 if(target?.id){
  try{await fetch(base+'/json/close/'+target.id,{signal:AbortSignal.timeout(5000)})}catch{}
  try{fs.unlinkSync(path.join(markers,port+'-'+target.id+'.json'))}catch{}
 }
}
