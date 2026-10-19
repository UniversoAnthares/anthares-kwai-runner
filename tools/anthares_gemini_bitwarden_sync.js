#!/usr/bin/env node
'use strict';
// Authenticated, remote-only Gemini key delivery; never logs credential values.
const fs=require('fs'), os=require('os'), path=require('path'), cp=require('child_process');
const sdk=require(path.join(process.env.RUNNER_TEMP||'/tmp','anthares-bws-sdk/node_modules/@bitwarden/sdk-napi'));
const project='87361776',testId='6edd06b7-ce2e-4519-905f-b4e800e4fe1a';
const secretName='ANTHARES_AI_GEMINI_PRODUCTION';
const sshPin='SHA256:G82n00KCkTp01cLSOaTFtg1CY9CBNJL5+kwGEEQ3NMM';
const root='/home/u566597497/domains/anthares.us/public_html';
const stage='/home/u566597497/.anthares-stage/ai-hub-20261019';
let phase='START',work,sshInfo,client;
function run(bin,args,opt={}){
 const r=cp.spawnSync(bin,args,{input:opt.input,encoding:'utf8',timeout:opt.timeout||32000,maxBuffer:700000,env:process.env});
 if(r.error||r.status!==0){
  const indicator=(r.stdout||'').match(/GEMINI_API_RESULT=ERROR_CODE_[a-z0-9_]+|SECRETS_SUBCLASS=FAIL|SECRETS_FAIL_CLOSED|AI_HUB_CLASSES=UNAVAILABLE|GEMINI_SETTINGS=UNAVAILABLE|GEMINI_API_RESULT=EMPTY/);
  if(indicator)throw Error('EXEC_FAILED_'+indicator[0]);
  if(/PHP Fatal error|Parse error|syntax error/i.test(r.stderr||''))throw Error('EXEC_FAILED_PHP_FATAL');
  if(/critical error|erro crítico/i.test(r.stderr||''))throw Error('EXEC_FAILED_WORDPRESS_CRITICAL');
  throw Error('EXEC_FAILED');
 }
 return r.stdout||'';
}
async function variable(n){
 const url='https://gitlab.com/api/v4/projects/'+project+'/variables/'+encodeURIComponent(n);
 const r=await fetch(url,{headers:{'PRIVATE-TOKEN':process.env.GITLAB_TOKEN},signal:AbortSignal.timeout(16000)});
 if(!r.ok)throw Error('GITLAB_VARIABLE_HTTP_'+r.status);
 const v=(await r.json()).value;
 if(typeof v!=='string'||!v)throw Error('GITLAB_VARIABLE_EMPTY');
 return v;
}
function ssh(cmd,input='',timeout=70000){
 const c=sshInfo;
 return run('ssh',['-p',c.port,'-i',c.key,'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+c.known,'-o','ConnectTimeout=10',c.user+'@'+c.host,cmd],{input,timeout});
}
function wpEval(localFile){
 const name=path.basename(localFile);
 if(!/^[a-zA-Z0-9-]+\.(php)$/.test(name))throw Error('INVALID_SCRIPT_NAME');
 const remote=stage+'/ci-'+name;
 ssh('umask 077; mkdir -p '+stage+'; chmod 700 '+stage+'; cat > '+remote,fs.readFileSync(localFile,'utf8'));
 try{
  return ssh('cd '+root+' && /opt/alt/php82/usr/bin/php /usr/local/bin/wp-cli-2.12.0.phar eval-file '+remote+' --path='+root+' --skip-themes','',110000);
 }finally{try{ssh('rm -f '+remote)}catch{}}
}
function data(r){if(!r||r.success===false)throw Error('BWS_SDK_OPERATION_FAILED');return r.data||r}
async function init(){
 if(!process.env.GITLAB_TOKEN||!process.env.BWS_ACCESS_TOKEN)throw Error('GITHUB_SECRETS_MISSING');
 work=fs.mkdtempSync(path.join(process.env.RUNNER_TEMP||os.tmpdir(),'anthares-gemini-'));
 fs.chmodSync(work,0o700);
 phase='READ_SSH_CONFIG';
 const d={};for(const n of ['ANTHARES_QA_SSH_HOST','ANTHARES_QA_SSH_USER','ANTHARES_QA_SSH_PORT','ANTHARES_QA_SSH_KEY'])d[n]=await variable(n);
 const key=path.join(work,'identity'),known=path.join(work,'known_hosts');
 fs.writeFileSync(key,d.ANTHARES_QA_SSH_KEY.replace(/\r\n/g,'\n').trim()+'\n',{mode:0o600});
 phase='VERIFY_SSH_HOST';
 const scanned=run('ssh-keyscan',['-T','12','-p',d.ANTHARES_QA_SSH_PORT,'-t','ed25519',d.ANTHARES_QA_SSH_HOST],{timeout:22000});
 fs.writeFileSync(known,scanned,{mode:0o600});
 if(!run('ssh-keygen',['-lf',known,'-E','sha256']).includes(sshPin))throw Error('SSH_PIN_FAILED');
 sshInfo={host:d.ANTHARES_QA_SSH_HOST,port:d.ANTHARES_QA_SSH_PORT,user:d.ANTHARES_QA_SSH_USER,key,known};
 phase='WORDPRESS_PRECHECK';
 const ready=ssh('test -f '+root+'/wp-config.php && test -f '+root+'/wp-content/mu-plugins/anthares-secrets-runtime-bridge.php && grep -q anthares_ai_providers '+root+'/wp-content/mu-plugins/anthares-secrets-runtime-bridge.php && echo SITE_READY');
 if(!ready.includes('SITE_READY'))throw Error('WORDPRESS_BRIDGE_MISSING');
 console.log('GEMINI_REMOTE_SSH_PINNED=PASS');
 phase='BITWARDEN_AUTH';
 client=new sdk.BitwardenClient({apiUrl:'https://api.bitwarden.com',identityUrl:'https://identity.bitwarden.com',userAgent:'anthares-gemini-sync',deviceType:sdk.DeviceType.SDK});
 const login=await client.auth().loginAccessToken(process.env.BWS_ACCESS_TOKEN.trim(),path.join(work,'bws-state'));if(login?.success===false)throw Error('BWS_AUTH_FAILED');
 const test=data(await client.secrets().get(testId));
 if(!test.organizationId||!test.projectId)throw Error('BWS_PROJECT_SCOPE_MISSING');
 console.log('GEMINI_BWS_MACHINE_AUTH=PASS');
 return {org:test.organizationId,proj:test.projectId};
}
async function selectOrRead(ids){
 phase='BITWARDEN_LOOKUP';
 const raw=data(await client.secrets().list(ids.org));
 const arr=Array.isArray(raw?.data)?raw.data:Array.isArray(raw)?raw:[];
 const matches=arr.filter(x=>x.key===secretName);
 if(matches.length>1)throw Error('AMBIGUOUS_BWS_SECRET');
 if(matches.length===1){
  const old=data(await client.secrets().get(matches[0].id));
  if(typeof old.value!=='string'||old.value.trim().length<16)throw Error('BWS_SECRET_EMPTY');
  console.log('GEMINI_BWS_SOURCE=EXISTING');
  return old.value.trim();
 }
 phase='SELECT_VALID_GEMINI_KEY';
 const response=wpEval('tools/anthares-gemini-select.php');
 const m=response.match(/SELECTED_GEMINI_KEY_BASE64=([A-Za-z0-9+/=]+)/);
 if(!m)throw Error('GEMINI_CREDENTIAL_NONE_VERIFIED');
 const value=Buffer.from(m[1],'base64').toString('utf8').trim();
 if(value.length<16||/[\r\n\0]/.test(value))throw Error('GEMINI_CREDENTIAL_MALFORMED');
 phase='BITWARDEN_CREATE';
 const made=data(await client.secrets().create(ids.org,secretName,value,'Anthares Gemini production; synchronized via pinned SSH', [ids.proj]));
 if(!made.id)throw Error('BWS_CREATE_ID_MISSING');
 const check=data(await client.secrets().get(made.id));
 if(check.value!==value)throw Error('BWS_WRITE_READBACK_FAILED');
 console.log('GEMINI_BWS_CREATED_VERIFIED=PASS');
 return value;
}
function installOnHost(value){
 phase='SYNC_SECRET_TO_HOST';
 const lines=[
  'set -eu',
  'umask 077',
  'd="$HOME/.anthares-secrets/ai-hub"',
  'mkdir -p "$d"',
  'chmod 700 "$HOME/.anthares-secrets" "$d"',
  't=$(mktemp "$d/.gemini.XXXXXX")',
  'cat > "$t"',
  'test -s "$t"',
  'chmod 600 "$t"',
  'mv -f "$t" "$d/gemini.secret"',
  'test "$(stat -c %a "$d/gemini.secret")" = 600',
  'echo GEMINI_SECRET_FILE=PASS'
 ];
 const q="bash -c '"+lines.join('; ').replace(/'/g,"'\\''")+"'";
 const output=ssh(q,value);
 if(!output.includes('GEMINI_SECRET_FILE=PASS'))throw Error('SECRET_DELIVERY_FAILED');
 console.log('GEMINI_HOST_SECRET_INSTALLED=PASS');
}
function testCanary(){
 phase='GEMINI_REAL_GENERATION';
 const result=wpEval('tools/anthares-gemini-canary.php');
 if(!result.includes('ANTHARES_GEMINI_REAL_REQUEST=PASS'))throw Error('PROVIDER_REAL_REQUEST_NOT_VERIFIED');
 console.log('GEMINI_REAL_PRODUCTION_CANARY=PASS');
}
function activate(){
 phase='WORDPRESS_ACTIVATION';
 if(process.env.ANTHARES_GEMINI_ACTIVATE_PRODUCTION!=='1'){
  console.log('GEMINI_PRODUCTION_ACTIVATION=STAGED_ONLY');
  return;
 }
 const res=ssh('bash -s',fs.readFileSync('tools/anthares-gemini-activate.sh','utf8'),85000);
 if(!res.includes('ANTHARES_WORDPRESS_GEMINI_OPTIN=PASS')&&!res.includes('PRODUCTION_OPTIN_ALREADY_PRESENT'))throw Error('WORDPRESS_ACTIVATION_FAILED');
 console.log('GEMINI_PRODUCTION_ACTIVATED=PASS');
}
(async()=>{
 try{
  const ids=await init();
  const value=await selectOrRead(ids);
  installOnHost(value);
  testCanary();
  activate();
  console.log('ANTHARES_GEMINI_BITWARDEN_INTEGRATION=PASS');
 }catch(e){
  console.error('ANTHARES_GEMINI_SYNC_FAILED_STAGE='+phase);
  console.error('ANTHARES_GEMINI_SYNC_ERROR_TYPE='+String(e?.message||'UNKNOWN').replace(/[^a-zA-Z0-9_]/g,'').slice(0,64));
  process.exitCode=1;
 }finally{
  if(work)try{fs.rmSync(work,{recursive:true,force:true})}catch{}
 }
})();
