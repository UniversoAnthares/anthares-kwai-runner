import assert from 'node:assert/strict';
import fs from 'node:fs';
const source=fs.readFileSync(new URL('../infra/neon-cortes-queue/index.mjs',import.meta.url),'utf8');
assert.match(source,/const dbTrue=v=>v===true/);
for(const line of ["dbTrue(v[0]?.active)","dbTrue(rows[0]?.provider_blocked)","dbTrue(activeBlock[0]?.blocked)"])
  assert.ok(source.includes(line),line);
assert.ok(!source.includes('Boolean(rows[0]?.provider_blocked)'));
assert.ok(!source.includes('Boolean(activeBlock[0]?.blocked)'));
const dbTrue=v=>v===true||v===1||v==='t'||v==='true'||v==='1';
for(const v of [false,'f','false','0',null,undefined,0,''])assert.equal(dbTrue(v),false,JSON.stringify(v));
for(const v of [true,'t','true','1',1])assert.equal(dbTrue(v),true,JSON.stringify(v));
console.log('NEON_BUFFER_BOOLEAN_POLICY_OK');
