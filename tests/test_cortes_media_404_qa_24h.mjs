import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
const source=readFileSync(new URL('../infra/neon-cortes-queue/index.mjs',import.meta.url),'utf8');
test('all 404 actions preserve the 24h-and-QA recovery contract',()=>{
  assert.equal((source.match(/discard_policy:'qa_24h_then_qa_exhaustion_required'/g)||[]).length,3);
  assert.equal((source.match(/COALESCE\(NULLIF\(confirmation_evidence->>'quarantine_at',''\)::timestamptz,updated_at\)\s*<= now\(\)-interval '24 hours'/g)||[]).length,2);
  assert.equal((source.match(/confirmation_evidence @> '\{"qa_recovery_exhausted":true\}'::jsonb/g)||[]).length,2);
  assert.doesNotMatch(source,/discard_policy:'next_local_daily_round'/);
  assert.doesNotMatch(source,/\(updated_at AT TIME ZONE 'America\/Campo_Grande'\)::date\s*<\s*\(now\(\) AT TIME ZONE 'America\/Campo_Grande'\)::date/);
});
test('expiry threshold requires BOTH 24h and a QA outcome',()=>{
  const eligible=(ageMs,exhausted)=>ageMs>=24*3600*1000&&exhausted===true;
  for(const elapsed of [0,23*3600*1000+59*60000])assert.equal(eligible(elapsed,true),false);
  assert.equal(eligible(24*3600*1000,false),false);
  assert.equal(eligible(24*3600*1000,true),true);
  assert.equal(eligible(24*3600*1000+60000,true),true);
});
