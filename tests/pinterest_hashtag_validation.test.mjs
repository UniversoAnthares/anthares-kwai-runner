import assert from 'node:assert/strict';
import fs from 'node:fs';
const neon=fs.readFileSync(new URL('../infra/neon-cortes-queue/index.mjs',import.meta.url),'utf8');
const marker=String.raw`/^#[\p{L}0-9_]{2,40}$/u.test(x)`;
const forbidden=String.raw`/^#[\\p{L}0-9_]{2,40}$/u.test(x)`;
assert.ok(neon.includes(marker),'Neon must use the real Unicode property escape');
assert.ok(!neon.includes(forbidden),'Double escaped Unicode hashtag regex is invalid');
const valid=/^#[\p{L}0-9_]{2,40}$/u;
for(const tag of ['#Literatura','#CríticaLiterária','#Kafka','#AnáliseFilosófica'])
  assert.equal(valid.test(tag),true,tag);
for(const tag of ['#tag com espaço','#','#hashtag!'])
  assert.equal(valid.test(tag),false,tag);
console.log('PINTEREST_UNICODE_HASHTAG_REGEX_OK');
