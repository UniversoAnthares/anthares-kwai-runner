import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import handler from '../vercel-ara-primary/api/forgejo-identity-proof.mjs';

const {publicKey,privateKey}=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
const kid='item6-fixture';
const jwk=publicKey.export({format:'jwk'});
Object.assign(jwk,{kid,alg:'RS256',use:'sig'});
const expectedKeys='https://anthares.us/forgejo/api/actions/.well-known/keys';
let fetched=0;
globalThis.fetch=async (url)=>{assert.equal(url,expectedKeys);fetched++;return {ok:true,json:async()=>({keys:[jwk]})};};
const aud='urn:anthares:forgejo:identity-proof:v1';
const iss='https://anthares.us/forgejo/api/actions';
const now=Math.floor(Date.now()/1000);
const repoSandbox='anthares-admin/anthares-ci-sandbox';
const repoTikTok='anthares-admin/anthares-tiktok-forgejo';
function sign(repo,work,overrides={}) {
  const body={iss,aud,repository:repo,repository_owner:'anthares-admin',
    sub:`repo:${repo}:ref:refs/heads/main`,ref:'refs/heads/main',
    workflow_ref:`${repo}/.forgejo/workflows/${work}@refs/heads/main`,
    event_name:'workflow_dispatch',iat:now-5,exp:now+300,...overrides};
  const header=Buffer.from(JSON.stringify({alg:'RS256',kid})).toString('base64url');
  const payload=Buffer.from(JSON.stringify(body)).toString('base64url');
  const sig=crypto.sign('RSA-SHA256',Buffer.from(header+'.'+payload),privateKey).toString('base64url');
  return header+'.'+payload+'.'+sig;
}
async function request(jwt,method='GET') {
  let body,status;
  const res={setHeader(){},end(v){body=JSON.parse(v)},set statusCode(x){status=x}};
  await handler({method,headers:{authorization:'Bearer '+jwt}},res);
  return {status,body};
}
assert.equal((await request(sign(repoSandbox,'forgejo-identity-proof.yml'))).status,200);
assert.deepEqual((await request(sign(repoTikTok,'item6-hostinger-readonly-standby.yml'))).body,{ok:true,provider:'forgejo',role:'identity-proof'});
for (const [repo,workflow,overrides] of [
  [repoTikTok,'tiktok-forgejo-universo.yml',{}],
  [repoTikTok,'tiktok-forgejo-lucas4.yml',{}],
  [repoTikTok,'forgejo-identity-proof.yml',{}],
  [repoTikTok,'item6-hostinger-readonly-standby.yml',{aud:'https://anthares-remote-primary.vercel.app/api/cortes-tiktok'}],
  [repoTikTok,'item6-hostinger-readonly-standby.yml',{event_name:'schedule'}],
  [repoTikTok,'item6-hostinger-readonly-standby.yml',{ref:'refs/heads/feature'}],
  [repoTikTok,'item6-hostinger-readonly-standby.yml',{repository_owner:'unknown'}],
  [repoTikTok,'item6-hostinger-readonly-standby.yml',{exp:now-1}],
  ['attacker/other','item6-hostinger-readonly-standby.yml',{}]
]) assert.equal((await request(sign(repo,workflow,overrides))).status,401,`${repo} ${workflow} ${JSON.stringify(overrides)}`);
assert.equal((await request(sign(repoTikTok,'item6-hostinger-readonly-standby.yml'),'POST')).status,405);
const tampered=sign(repoTikTok,'item6-hostinger-readonly-standby.yml');
const p=tampered.split('.');p[2]=p[2].slice(0,-5)+'abcde';
assert.equal((await request(p.join('.'))).status,401);
assert.ok(fetched>=2);
console.log('FORGEJO_TIKTOK_READONLY_SCOPE_TESTS_PASS=13');
