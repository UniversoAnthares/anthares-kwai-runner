const test=require('node:test'),assert=require('node:assert/strict');
const {validateTask,validateChanges,buildInstructions}=require('./anthares_free_claude_task');
const {MODELS,PORT}=require('./anthares_free_claude_bootstrap');
test('free models, distinct fallback',()=>{
  for(const role of ['plan','edit']){
    assert.equal(MODELS[role].length,2);
    assert.notEqual(MODELS[role][0],MODELS[role][1]);
    assert(MODELS[role].every(x=>x.startsWith('gemini/gemini-2.5-flash')));
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
