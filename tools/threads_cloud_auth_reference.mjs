// Stores a non-secret cloud credential reference on Windows.
// Browser cookies, OAuth bearer values and refresh tokens never leave their vault.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const config=JSON.parse(fs.readFileSync(path.resolve(here,'../config/threads-cloud-auth-reference.json'),'utf8'));
const root=process.env.CORTES_THREADS_LOCAL_ROOT||'D:\\AntharsWork\\cortes-social-browser-20261020';
const outDir=path.join(root,'auth-references');
const outFile=path.join(outDir,'threads-cloud-reference.json');
function safeRead(file){
 try{return JSON.parse(fs.readFileSync(file,'utf8'))}catch{return null}
}
function validate(){
 if(config.schema!=='anthares.threads.auth-reference.v1'||config.account!=='universoanthares'||
    config.credential_kind!=='oauth_access_token'||config.token_storage!=='bitwarden_secrets_manager'||
    config.cloud_environment_variable!=='THREADS_ACCESS_TOKEN'||
    config.copy_browser_cookies!==false||config.copy_access_token_to_folder!==false||
    config.requires_live_identity_check!==true||config.requires_neon_fencing!==true)
   throw Error('INVALID_CREDENTIAL_REFERENCE_POLICY');
}
export function status(){
 validate();
 const ledger=safeRead(path.join(root,'threads-ledger.json'))||{items:{}};
 const rows=Object.values(ledger.items||{});
 return {
  schema:'anthares.threads.cloud-reference-status.v1',
  updated_at:new Date().toISOString(),
  account:config.account,
  auth_source:config.token_storage,
  credential_reference:'config/threads-cloud-auth-reference.json',
  credential_value_present:false,
  browser_cookies_present:false,
  live_cloud_authentication:'NOT_VERIFIED_BY_THIS_FILE',
  local_confirmed_count:rows.filter(x=>x.status==='published').length,
  local_uncertain_count:rows.filter(x=>x.status==='submitting_uncertain').length,
  last_local_confirmed_at:ledger.lastPublished||null,
  cloud_requires_live_token_proof:config.requires_live_identity_check,
  cloud_requires_shared_lease:config.requires_neon_fencing
 };
}
export function writeStatus(){
 const body=status();
 fs.mkdirSync(outDir,{recursive:true});
 const tmp=outFile+'.tmp-'+process.pid;
 fs.writeFileSync(tmp,JSON.stringify(body,null,2)+'\n',{encoding:'utf8',mode:0o600});
 fs.renameSync(tmp,outFile);
 try{fs.chmodSync(outFile,0o600)}catch{}
 return body;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const result=process.argv.includes('--write')?writeStatus():status();
  console.log(JSON.stringify(result));
 }catch(err){
  console.error('THREADS_AUTH_REFERENCE_FAIL='+String(err?.message||err).slice(0,120));
  process.exitCode=2;
 }
}
