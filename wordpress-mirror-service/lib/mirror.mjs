import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import git from 'isomorphic-git';
import http from 'isomorphic-git/http/node';

export const SOURCE='https://github.com/UniversoAnthares/anthares-wordpress.git';
export const DESTINATION='https://gitlab.com/UniversoAnthares/anthares-wordpress.git';
const ZERO='0'.repeat(40);
const AUTHOR={name:'Anthares Safe Mirror',email:'mirror@anthares.invalid'};
export class MirrorError extends Error { constructor(code){super(code);this.code=code;} }
export function validRef(ref){return ref==='main'||/^validation\/mirror-20261018[-a-z0-9]*$/.test(ref);}
export function authorized(header,secret){const a=Buffer.from(String(header||'')),b=Buffer.from('Bearer '+String(secret||''));return String(secret||'').length>=32&&a.length===b.length&&crypto.timingSafeEqual(a,b);}
export function classify(source,destination,sourceInDestination,destinationInSource){
 if(source===destination)return 'IN_SYNC';
 if(sourceInDestination)return 'IN_SYNC_PRESERVING_DESTINATION';
 if(destinationInSource)return 'FAST_FORWARD';
 return 'MERGE_REQUIRED';
}
const gitOptions=(dir)=>({fs,dir,cache:{}});
const authFor=(url,env)=>()=>({username:url===SOURCE?'x-access-token':'oauth2',password:url===SOURCE?env.GITHUB_READ_TOKEN:env.GITLAB_WRITE_TOKEN});
const network=(url,env)=>({url,http,onAuth:authFor(url,env),headers:{'User-Agent':'AntharesWordPressMirror/1.0'}});
async function refs(url,env){return git.listServerRefs({...network(url,env),forPush:url===DESTINATION});}
async function remoteOid(url,ref,env){return (await refs(url,env)).find(x=>x.ref==='refs/heads/'+ref)?.oid||null;}
async function fetchRef(dir,url,ref,remote,env,depth){
 return git.fetch({...gitOptions(dir),...network(url,env),ref,remote,singleBranch:true,tags:false,...(depth?{depth}:{} )});
}
async function localRef(dir,name,oid){await git.writeRef({...gitOptions(dir),ref:'refs/heads/'+name,value:oid,force:true});}
async function pushExpected(dir,name,oid,expected,env){
 const ref='send-'+crypto.randomUUID();await localRef(dir,ref,oid);
 const result=await git.push({...gitOptions(dir),...network(DESTINATION,env),ref,remoteRef:name,
  onPrePush:({remoteRef})=>{if(remoteRef.oid!==(expected||ZERO))throw new MirrorError('DESTINATION_CHANGED');return true;}});
 if(!result.ok)throw new MirrorError('PUSH_REJECTED');
}
async function stateCommit(dir,parent,record){
 const tree=await git.writeTree({...gitOptions(dir),tree:[]});
 return git.writeCommit({...gitOptions(dir),commit:{tree,parent:parent?[parent]:[],author:{...AUTHOR,timestamp:Math.floor(Date.now()/1000),timezoneOffset:0},committer:{...AUTHOR,timestamp:Math.floor(Date.now()/1000),timezoneOffset:0},message:JSON.stringify(record)+'\n'}});
}
async function readRecord(dir,oid){const {commit}=await git.readCommit({...gitOptions(dir),oid});try{return JSON.parse(commit.message);}catch{throw new MirrorError('INVALID_LOCK_RECORD');}}
async function acquire(dir,ref,runId,env,trigger){
 const name='mirror-state/wordpress/'+ref.replaceAll('/','-');
 const old=await remoteOid(DESTINATION,name,env);
 if(old){await fetchRef(dir,DESTINATION,name,'state',env,1);const record=await readRecord(dir,old);if(record.state==='running'&&Number(record.expires_at)>Date.now())throw new MirrorError('LOCK_BUSY');}
 const record={state:'running',run_id:runId,ref,started_at:new Date().toISOString(),expires_at:Date.now()+600000,trigger};
 const oid=await stateCommit(dir,old,record);await pushExpected(dir,name,oid,old,env);
 return {name,oid,record};
}
async function release(dir,lock,result,env){
 if(await remoteOid(DESTINATION,lock.name,env)!==lock.oid)throw new MirrorError('LOCK_OWNERSHIP_LOST');
 const oid=await stateCommit(dir,lock.oid,{...lock.record,state:'finished',expires_at:0,finished_at:new Date().toISOString(),result});
 await pushExpected(dir,lock.name,oid,lock.oid,env);
 return oid;
}
export async function changedPaths(dir,before,after){
 if(!before)return (await git.listFiles({...gitOptions(dir),ref:after})).sort();
 const changes=await git.walk({...gitOptions(dir),trees:[git.TREE({ref:before}),git.TREE({ref:after})],map:async(filepath,[a,b])=>{
  if(filepath==='.')return;
  const at=await a?.type(),bt=await b?.type();if(at==='tree'||bt==='tree')return;
  if((await a?.oid())!==(await b?.oid()))return filepath;
 }});
 return changes.filter(Boolean).sort();
}
export async function candidate(dir,source,destination){
 if(!destination)return {oid:source,kind:'CREATED'};
 const [sourceInDestination,destinationInSource]=await Promise.all([
  source===destination?true:git.isDescendent({...gitOptions(dir),oid:destination,ancestor:source}),
  source===destination?true:git.isDescendent({...gitOptions(dir),oid:source,ancestor:destination})]);
 const kind=classify(source,destination,sourceInDestination,destinationInSource);
 if(kind.startsWith('IN_SYNC'))return{oid:destination,kind};
 if(kind==='FAST_FORWARD')return{oid:source,kind};
 try{
  const result=await git.merge({...gitOptions(dir),ours:destination,theirs:source,author:AUTHOR,committer:AUTHOR,noUpdateBranch:true,abortOnConflict:true,message:'chore(mirror): preserve GitLab changes and merge GitHub source [skip ci]'});
  if(!result.oid)throw new MirrorError('MERGE_NOT_PROVEN');
  return {oid:result.oid,kind:'MERGED_PRESERVING_BOTH'};
 }catch(error){throw new MirrorError(/conflict|merge|base|ancestor/i.test(error.code||error.name||'')?'CONTENT_CONFLICT':error.code||'MERGE_FAILED');}
}
export async function synchronize({env=process.env,ref='main',trigger={type:'manual'},fault='',runId=crypto.randomUUID()}={}){
 if(!validRef(ref))throw new MirrorError('REF_NOT_ALLOWED');
 if(!env.GITHUB_READ_TOKEN||!env.GITLAB_WRITE_TOKEN)throw new MirrorError('CREDENTIAL_NOT_CONFIGURED');
 if(fault&&ref==='main')throw new MirrorError('FAULT_TEST_REQUIRES_VALIDATION_REF');
 const dir=await fs.promises.mkdtemp(path.join(os.tmpdir(),'anthares-wordpress-mirror-'));
 let lock,result;const began=Date.now();
 try{
  await git.init({...gitOptions(dir),defaultBranch:'work'});
  lock=await acquire(dir,ref,runId,env,trigger);
  if(fault==='authentication')throw new MirrorError('CONTROLLED_AUTH_FAILURE');
  const source=await remoteOid(SOURCE,ref,env);
  if(!source)throw new MirrorError('SOURCE_REF_MISSING');
  const destination=await remoteOid(DESTINATION,ref,env);
  if(!destination&&ref==='main')throw new MirrorError('DESTINATION_MAIN_MISSING');
  await fetchRef(dir,SOURCE,ref,'source',env);
  if(destination)await fetchRef(dir,DESTINATION,ref,'destination',env);
  const next=await candidate(dir,source,destination);
  const changes=await changedPaths(dir,destination,next.oid);
  const backup=destination&&destination!==next.oid?'backup/auto-mirror/'+ref.replaceAll('/','-')+'/'+destination:null;
  // Both providers and the lock are fenced immediately before any branch update.
  if(await remoteOid(SOURCE,ref,env)!==source)throw new MirrorError('SOURCE_CHANGED');
  if(await remoteOid(DESTINATION,ref,env)!==destination)throw new MirrorError('DESTINATION_CHANGED');
  if(await remoteOid(DESTINATION,lock.name,env)!==lock.oid)throw new MirrorError('LOCK_OWNERSHIP_LOST');
  if(backup){
   const oldBackup=await remoteOid(DESTINATION,backup,env);
   if(oldBackup&&oldBackup!==destination)throw new MirrorError('BACKUP_REF_CONFLICT');
   if(!oldBackup)await pushExpected(dir,backup,destination,null,env);
  }
  if(next.oid!==destination)await pushExpected(dir,ref,next.oid,destination,env);
  const actual=await remoteOid(DESTINATION,ref,env);
  if(actual!==next.oid)throw new MirrorError('POST_PUSH_VERIFICATION_FAILED');
  const commit=(await git.readCommit({...gitOptions(dir),oid:actual})).commit;
  const sourceCommit=(await git.readCommit({...gitOptions(dir),oid:source})).commit;
  if(actual!==source&&!await git.isDescendent({...gitOptions(dir),oid:actual,ancestor:source}))throw new MirrorError('SOURCE_HISTORY_NOT_PRESERVED');
  if(destination&&actual!==destination&&!await git.isDescendent({...gitOptions(dir),oid:actual,ancestor:destination}))throw new MirrorError('DESTINATION_HISTORY_NOT_PRESERVED');
  result={ok:true,run_id:runId,ref,outcome:next.kind,source_head:source,destination_before:destination,destination_head:actual,source_tree:sourceCommit.tree,destination_tree:commit.tree,changed_paths:changes,backup_ref:backup,duration_ms:Date.now()-began};
 }catch(error){result={ok:false,run_id:runId,ref,error:String(error.code||'SYNC_FAILED').slice(0,100),duration_ms:Date.now()-began};}
 try{if(lock)result.audit_commit=await release(dir,lock,result,env);}catch{result.audit_error='AUDIT_WRITE_FAILED';}
 await fs.promises.rm(dir,{recursive:true,force:true});
 return result;
}
export async function latest({env=process.env,ref='main'}={}){
 if(!validRef(ref))throw new MirrorError('REF_NOT_ALLOWED');
 const dir=await fs.promises.mkdtemp(path.join(os.tmpdir(),'anthares-mirror-status-'));
 try{await git.init({...gitOptions(dir)});const name='mirror-state/wordpress/'+ref.replaceAll('/','-');const oid=await remoteOid(DESTINATION,name,env);if(!oid)return{state:'never_run',ref};await fetchRef(dir,DESTINATION,name,'state',env,1);return{...(await readRecord(dir,oid)),audit_commit:oid};}
 finally{await fs.promises.rm(dir,{recursive:true,force:true});}
}
