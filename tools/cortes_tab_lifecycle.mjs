import fs from 'node:fs';
import path from 'node:path';
const base='D:\\AntharsWork\\cortes-social-browser-20261020';
const dir=path.join(base,'chrome-owned-tabs');
const log=path.join(base,'chrome-tab-cleanup.log');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const ownPath=(port,id)=>path.join(dir,port+'-'+id+'.json');
const valid=(port,id)=>port===9225&&/^[a-f0-9]{32}$/i.test(id);
export function claimTab(port,id){
 if(!valid(port,id))throw Error('INVALID_CORTES_CDP_TARGET');
 fs.mkdirSync(dir,{recursive:true});
 fs.writeFileSync(ownPath(port,id),JSON.stringify({port,id,pid:process.pid,created:Date.now()}),{flag:'wx'});
}
async function openTabs(port){
 const r=await fetch('http://127.0.0.1:'+port+'/json/list',{signal:AbortSignal.timeout(4000)});
 if(!r.ok)throw Error('CDP_LIST_'+r.status);
 return await r.json();
}
export async function releaseTab(port,id){
 if(!valid(port,id))return false;
 for(let n=0;n<3;n++){
  try{
   const pages=await openTabs(port);
   if(!pages.some(t=>t.id===id)){
    try{fs.unlinkSync(ownPath(port,id))}catch{}
    return true;
   }
   await fetch('http://127.0.0.1:'+port+'/json/close/'+id,{signal:AbortSignal.timeout(4000)});
  }catch{}
  await pause(350);
 }
 try{
  if(!(await openTabs(port)).some(t=>t.id===id)){
   try{fs.unlinkSync(ownPath(port,id))}catch{}
   return true;
  }
 }catch{}
 return false;
}
function pidIsAlive(pid){
 if(!Number.isSafeInteger(pid)||pid<=0)return false;
 try{process.kill(pid,0);return true}catch(e){return e?.code==='EPERM'}
}
export async function reapOrphans(){
 if(!fs.existsSync(dir))return {scanned:0,closed:0};
 let scanned=0,closed=0;
 for(const name of fs.readdirSync(dir)){
  if(!/^9225-[a-f0-9]{32}\.json$/i.test(name))continue;
  const file=path.join(dir,name);
  let item;try{item=JSON.parse(fs.readFileSync(file,'utf8'))}catch{continue}
  if(!valid(item.port,item.id))continue;
  scanned++;
  if(Date.now()-Number(item.created)<120000||pidIsAlive(Number(item.pid)))continue;
  try{
   const tabs=await openTabs(item.port);
   const target=tabs.find(t=>t.id===item.id);
   if(target && !/^https:\/\/www\.(?:instagram|threads)\.com\//i.test(target.url))continue;
   if(await releaseTab(item.port,item.id)){
    closed++;
    fs.appendFileSync(log,new Date().toISOString()+' ORPHAN_CLOSED port='+item.port+' tab='+item.id+'\n');
   }
  }catch{}
 }
 return {scanned,closed};
}