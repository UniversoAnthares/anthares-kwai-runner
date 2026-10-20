const test=require('node:test'),assert=require('node:assert/strict');
const {validateTask,validateChanges,buildInstructions,buildClaudeArgs}=require('./anthares_free_claude_task');
const {MODELS,PORT,extractAssistantText,probeRouter}=require('./anthares_free_claude_bootstrap');
test('free models, distinct fallback',()=>{
  for(const role of ['plan','edit']){
    assert.equal(MODELS[role].length,3);
    assert.notEqual(MODELS[role][0],MODELS[role][1]);
    assert(MODELS[role].every(x=>/^gemini\/gemini-3(?:\.8-flash|\.5-flash-lite|-flash-preview)$/.test(x)));
  }
  assert.equal(PORT,20128);
});
test('strict path, prompt and mode',()=>{
  for(const scope of ['.github/workflows/x.yml','tools/../.github/x','docs/.env','secrets/key','tools/node_modules/q'])
    assert.throws(()=>validateTask({mode:'edit',prompt:'hello',scope}));
  assert.throws(()=>validateTask({mode:'plan',prompt:'x'.repeat(7501)}));
  assert.throws(()=>validateTask({mode:'superuser',prompt:'good'}));
  assert.equal(validateTask({mode:'edit',prompt:'fix',scope:'docs/test.md'}).scope,'docs/test.md');
});
test('file change gate requires exact path only',()=>{
  assert.equal(validateChanges('docs/a.md',['docs/a.md']),true);
  for(const paths of [[],['docs/a.md','docs/b.md'],['.github/x'],['docs/b.md']])
    assert.equal(validateChanges('docs/a.md',paths),false);
});
test('instructions forbid shell and protect scope',()=>{
  const t=buildInstructions({mode:'edit',prompt:'fix',scope:'tools/z.js'});
  assert.match(t,/Edit ONLY this one file: tools\/z.js/);
  assert.match(t,/No media publication, deploy, shell tool/);
});

test('9Router streaming Anthropic, OpenAI and JSON responses require generated text',()=>{
  assert.equal(extractAssistantText(JSON.stringify({content:[{type:'text',text:'OK'}]})),'OK');
  assert.equal(extractAssistantText('event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"O"}}\n\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"K"}}\n\ndata: [DONE]\n'),'OK');
  assert.equal(extractAssistantText('data: {"choices":[{"delta":{"content":"O"}}]}\n\ndata: {"choices":[{"delta":{"content":"K"}}]}\n'),'OK');
  assert.equal(extractAssistantText(JSON.stringify({error:{message:'denied'}})),'');
  assert.equal(extractAssistantText('data: {"type":"message_start","message":{"id":"abc","content":[]}}\n\n'),'');
  assert.equal(extractAssistantText(''), '');
});

test('canary disables all tools, production modes keep tight allowlist',()=>{
  const plan={mode:'plan'}, edit={mode:'edit'};
  const smoke=buildClaudeArgs(plan,'anthares-free-plan',true);
  assert.equal(smoke[smoke.indexOf('--tools')+1],'');
  assert.equal(smoke[smoke.indexOf('--max-turns')+1],'3');
  assert.equal(smoke[smoke.indexOf('--permission-mode')+1],'default');
  const a=buildClaudeArgs(plan,'anthares-free-plan');
  assert.equal(a[a.indexOf('--tools')+1],'Read,Glob,Grep');
  assert.equal(a[a.indexOf('--max-turns')+1],'20');
  const b=buildClaudeArgs(edit,'anthares-free-edit');
  assert.equal(b[b.indexOf('--tools')+1],'Read,Edit,Write,Glob,Grep');
  assert.equal(b[b.indexOf('--disallowedTools')+1],'mcp__*');
  assert(!b.includes('Bash'));
});

test('9Router harmless readiness probe retries a timeout and requires actual generated text',async()=>{
 let calls=0;
 const prior=console.log;
 const events=[];
 console.log=(...args)=>events.push(args.join(' '));
 try{
  await probeRouter('anthares-free-plan','not-a-real-key',{
   attempts:2,delay:async()=>{},
   request:async(url,init)=>{
    calls++;
    assert.match(url,/^http:\/\/127\.0\.0\.1:20128\/v1\/messages$/);
    assert.equal(init.method,'POST');
    if(calls===1){const e=new Error('deadline');e.name='TimeoutError';throw e}
    return {ok:true,status:200,headers:{get:()=> 'text/event-stream'},
      text:async()=> 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"OK"}}\n\n'};
   }
  });
 }finally{console.log=prior}
 assert.equal(calls,2);
 assert(events.includes('ANTHARES_FREE_9ROUTER_REAL_INFERENCE=PASS'));
 assert(events.includes('ANTHARES_FREE_9ROUTER_RECOVERED_AFTER_RETRY=PASS'));
});
test('9Router non-retryable 400 or empty success cannot be passed off as inference',async()=>{
 for(const status of [400,200]){
  let calls=0;
  const prev=console.log;console.log=()=>{};
  try{
   await assert.rejects(probeRouter('anthares-free-plan','fake',{
    attempts:3,delay:async()=>{},
    request:async()=>{calls++;return {ok:status===200,status,headers:{get:()=> 'application/json'},text:async()=> '{"error":"no generated text"}'};}
   }),/ROUTER_INFERENCE_FAILED_HTTP_/);
  }finally{console.log=prev}
  assert.equal(calls,1);
 }
});
