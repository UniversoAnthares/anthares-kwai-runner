#!/usr/bin/env node
'use strict';
// One-file edit fence for a remote, free, ephemeral Claude Code runner.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const MAX_PROMPT=7500;
const DENIED=/(?:^|\/)(?:\.git|\.github|node_modules|test-hub|\.env|\.ssh|secrets|credentials|vault)(?:\/|$)/i;
function validateTask({mode,prompt,scope}){
  if(!['plan','edit'].includes(mode))throw Error('INVALID_MODE');
  if(typeof prompt!=='string'||!prompt.trim()||prompt.length>MAX_PROMPT||/[\x00-\x08\x0B-\x1F]/.test(prompt))throw Error('INVALID_PROMPT');
  if(mode==='edit'&&(
    typeof scope!=='string'||scope.length>170||
    !/^(?:tools|docs|ai-runners)\/[a-zA-Z0-9_./-]+$/.test(scope)||
    DENIED.test(scope)||scope.split('/').includes('..')
  ))throw Error('INVALID_OR_PROTECTED_SCOPE');
  return {mode,prompt:prompt.trim(),scope:scope||''};
}
function changedPaths(){
  const raw=cp.execFileSync('git',['status','--porcelain=v1','-uall'],{encoding:'utf8'}).trim();
  return raw?raw.split('\n').map(x=>x.slice(3).trim()).filter(Boolean):[];
}
function validateChanges(scope,paths){
  return paths.length>0&&paths.every(p=>p===scope&&!DENIED.test(p));
}
function buildInstructions(t){
  const policy='Read AGENTS.md and CLAUDE.md. This is a distributed protected system. Never open or expose secrets, runner credentials, environment files or authentication data. No media publication, deploy, shell tool, or production access.';
  return t.mode==='plan'?
    policy+'\nCreate a specific technical plan with validation and rollback. Do not write files.\nREQUEST:\n'+t.prompt:
    policy+'\nEdit ONLY this one file: '+t.scope+'. Preserve behavior and make the minimal change. If another file is required, explain and stop.\nREQUEST:\n'+t.prompt;
}
async function main(){
  const task=validateTask({mode:process.env.ANTHARES_TASK_MODE,prompt:process.env.ANTHARES_TASK_PROMPT,scope:process.env.ANTHARES_TASK_SCOPE});
  if(!process.env.ANTHROPIC_AUTH_TOKEN||!process.env.ANTHROPIC_BASE_URL)throw Error('ROUTER_NOT_CONFIGURED');
  const output=path.join(process.env.RUNNER_TEMP||'/tmp','anthares-claude-result.txt');
  const env={...process.env};
  for(const k of Object.keys(env))if(/^(BWS_|GITLAB_|GITHUB_TOKEN|GH_TOKEN|VERCEL_TOKEN|CLOUDFLARE_API_TOKEN)/.test(k))delete env[k];
  const allowed=task.mode==='plan'?['Read','Glob','Grep']:['Read','Edit','Write','Glob','Grep'];
  const args=['-p','--model',process.env.ANTHROPIC_MODEL,'--permission-mode',task.mode==='plan'?'plan':'acceptEdits','--max-turns','8','--output-format','text','--allowedTools',...allowed];
  const result=cp.spawnSync('claude',args,{
    input:buildInstructions(task),env,encoding:'utf8',timeout:80000,maxBuffer:240000,
    stdio:['pipe','pipe','pipe']
  });
  fs.writeFileSync(output,String(result.stdout||'').slice(0,30000),{mode:0o600});
  if(result.error||result.status!==0){
    const err=String(result.stderr||'').toLowerCase();
    let cause=result.error?.code==='ETIMEDOUT'?'TIMEOUT':
      /unauthorized|not logged in|authentication|login|401/.test(err)?'AUTH':
      /429|rate.limit|quota/.test(err)?'RATE_LIMIT':
      /model.*not.*found|unknown.model|model_not_found|invalid model/.test(err)?'MODEL':
      /gateway|connection refused|fetch failed|502|503|504/.test(err)?'GATEWAY':'UNKNOWN';
    console.error('ANTHARES_FREE_CLAUDE_FAILURE_CLASS='+cause);
    throw Error('CLAUDE_CODE_TASK_FAILED');
  }
  if(task.mode==='edit'){
    if(!validateChanges(task.scope,changedPaths()))throw Error('FILE_SCOPE_GATE_FAILED');
    console.log('ANTHARES_CLAUDE_EDITS_VALIDATED=PASS');
  }else console.log('ANTHARES_CLAUDE_PLAN=PASS');
  console.log('ANTHARES_FREE_CLAUDE_RUN=PASS');
}
if(require.main===module)main().catch(e=>{
  console.error('ANTHARES_FREE_TASK_ERROR='+(/^[A-Z_]+$/.test(e.message)?e.message:'UNKNOWN'));
  process.exitCode=1;
});
module.exports={validateTask,validateChanges,buildInstructions};
