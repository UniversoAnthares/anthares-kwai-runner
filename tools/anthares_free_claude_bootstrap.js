#!/usr/bin/env node
'use strict';
// Free, remote-only Claude Code bootstrap. No paid provider, VPS or PC runtime.
const fs=require('node:fs'), os=require('node:os'), path=require('node:path');
const crypto=require('node:crypto'), cp=require('node:child_process');
const MODELS=Object.freeze({
  plan:['gemini/gemini-2.5-flash','gemini/gemini-2.5-flash-lite'],
  edit:['gemini/gemini-2.5-flash-lite','gemini/gemini-2.5-flash'],
});
const PORT=20128;
const SECRET_NAME='ANTHARES_AI_GEMINI_PRODUCTION';
const TEST_SECRET_ID='6edd06b7-ce2e-4519-905f-b4e800e4fe1a';
async function readGeminiSecret(){
  if(!process.env.BWS_ACCESS_TOKEN)throw Error('BWS_TOKEN_MISSING');
  const root=process.env.RUNNER_TEMP||os.tmpdir();
  const sdk=require(path.join(root,'anthares-bws-sdk/node_modules/@bitwarden/sdk-napi'));
  const client=new sdk.BitwardenClient({
    apiUrl:'https://api.bitwarden.com',identityUrl:'https://identity.bitwarden.com',
    userAgent:'anthares-free-claude-code',deviceType:sdk.DeviceType.SDK
  });
  const tmp=fs.mkdtempSync(path.join(root,'anthares-bws-'));
  fs.chmodSync(tmp,0o700);
  const data=r=>{if(!r||r.success===false)throw Error('BWS_OPERATION_FAILED');return r.data||r};
  try{
    const login=await client.auth().loginAccessToken(process.env.BWS_ACCESS_TOKEN.trim(),path.join(tmp,'state'));
    if(login?.success===false)throw Error('BWS_AUTH_FAILED');
    const test=data(await client.secrets().get(TEST_SECRET_ID));
    if(!test.organizationId||!test.projectId)throw Error('BWS_PROJECT_MISMATCH');
    const listed=data(await client.secrets().list(test.organizationId));
    const entries=Array.isArray(listed.data)?listed.data:Array.isArray(listed)?listed:[];
    const selected=entries.filter(x=>x.key===SECRET_NAME);
    if(selected.length!==1)throw Error('BWS_SECRET_MISSING_OR_AMBIGUOUS');
    const secret=data(await client.secrets().get(selected[0].id));
    if(typeof secret.value!=='string'||secret.value.trim().length<16||/[\r\n\0]/.test(secret.value))throw Error('BWS_SECRET_INVALID');
    return secret.value.trim();
  }finally{fs.rmSync(tmp,{recursive:true,force:true})}
}
async function waitReady(proc){
  const until=Date.now()+60000;
  while(Date.now()<until){
    if(proc.exitCode!==null)throw Error('ROUTER_EXITED');
    try{
      const response=await fetch('http://127.0.0.1:'+PORT+'/api/health',{signal:AbortSignal.timeout(1200)});
      if(response.ok&&(await response.json()).ok===true)return;
    }catch{}
    await new Promise(resolve=>setTimeout(resolve,900));
  }
  throw Error('ROUTER_START_TIMEOUT');
}
function client(){
  const root=cp.execFileSync('npm',['root','-g'],{encoding:'utf8',timeout:9000}).trim();
  return require(path.join(root,'9router/src/cli/api/client.js'));
}
async function main(){
  if(!process.env.GITHUB_ENV||!process.env.RUNNER_TEMP)throw Error('GITHUB_RUNNER_REQUIRED');
  const mode=process.env.ANTHARES_TASK_MODE;
  if(!Object.hasOwn(MODELS,mode))throw Error('INVALID_MODE');
  const key=await readGeminiSecret();
  delete process.env.BWS_ACCESS_TOKEN;
  const home=fs.mkdtempSync(path.join(process.env.RUNNER_TEMP,'anthares-free-claude-'));
  fs.chmodSync(home,0o700);
  process.env.HOME=home;process.env.APPDATA=home;
  const passwd=crypto.randomBytes(32).toString('base64url');
  const router=cp.spawn('9router',['--host','127.0.0.1','--port',String(PORT),'--no-browser','--skip-update'],{
    env:{...process.env,INITIAL_PASSWORD:passwd,BROWSER:'none'},
    stdio:'ignore',detached:false,
  });
  try{
    await waitReady(router);
    const api=client();
    const provider=await api.createApiKeyProvider({
      provider:'gemini',name:'Anthares Gemini free only',
      apiKey:key,defaultModel:'gemini-2.5-flash',priority:1,
    });
    if(!provider.success)throw Error('GEMINI_PROVIDER_SETUP_FAILED');
    for(const [role,models] of Object.entries(MODELS)){
      const r=await api.createCombo({name:'anthares-free-'+role,models,kind:'llm'});
      if(!r.success)throw Error('FALLBACK_COMBO_SETUP_FAILED');
    }
    const access=await api.createApiKey('anthares-free-cli-ci');
    if(!access.success||!access.data?.key)throw Error('ROUTER_CLIENT_KEY_FAILED');
    const token=access.data.key;
    process.stdout.write('::add-mask::'+token+'\n');
    fs.appendFileSync(process.env.GITHUB_ENV,[
      'ANTHROPIC_BASE_URL=http://127.0.0.1:'+PORT+'/v1',
      'ANTHROPIC_AUTH_TOKEN='+token,
      'ANTHROPIC_MODEL=anthares-free-'+mode,
      'CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1',
      'CLAUDE_CODE_MAX_CONTEXT_TOKENS=60000',''
    ].join('\n'),{mode:0o600});
    router.unref();
    console.log('ANTHARES_FREE_ROUTER_READY=PASS');
    console.log('ANTHARES_FREE_FALLBACK_MODELS='+MODELS[mode].length);
  }catch(e){router.kill();throw e}
}
if(require.main===module)main().catch(e=>{
  console.error('ANTHARES_FREE_BOOTSTRAP_ERROR='+(/^[A-Z0-9_]+$/.test(e.message)?e.message:'INTERNAL'));
  process.exitCode=1;
});
module.exports={MODELS,PORT,waitReady};
