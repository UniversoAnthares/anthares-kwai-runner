import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {codebergConsumerRole as main} from '../infra/neon-cortes-tiktok/codeberg-oidc.mjs';
import {codebergConsumerRole as second} from '../infra/neon-cortes-lucasrosalem4/codeberg-oidc.mjs';
const {publicKey,privateKey}=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
const jwk=publicKey.export({format:'jwk'});
Object.assign(jwk,{kid:'test-key',alg:'RS256',use:'sig'});
globalThis.fetch=async u=>{
  assert.equal(u,'https://codeberg.org/api/actions/.well-known/keys');
  return {ok:true,json:async()=>({keys:[jwk]})};
};
const now=Math.floor(Date.now()/1000);
const repo='UniversoAnthares/anthares-kwai-runner';
const aud='https://anthares-remote-primary.vercel.app/api/cortes-tiktok';
function signed(overrides={}){
  const base={iss:'https://codeberg.org/api/actions',aud,
    repository:repo,ref:'refs/heads/main',exp:now+600,iat:now-5,
    event_name:'workflow_dispatch',
    workflow_ref:repo+'/.forgejo/workflows/cortes-tiktok-lucas4-codeberg.yml@refs/heads/main'};
  const header=Buffer.from(JSON.stringify({alg:'RS256',kid:'test-key'})).toString('base64url');
  const payload=Buffer.from(JSON.stringify({...base,...overrides})).toString('base64url');
  const signature=crypto.sign('RSA-SHA256',Buffer.from(header+'.'+payload),privateKey).toString('base64url');
  return {headers:{authorization:'Bearer '+header+'.'+payload+'.'+signature}};
}
assert.equal(await second(signed(),aud,'cortes-tiktok-lucas4-codeberg.yml'),'consumer');
assert.equal(await main(signed(),aud,'cortes-tiktok-universo-codeberg.yml'),'');
assert.equal(await main(signed({workflow_ref:repo+'/.forgejo/workflows/cortes-tiktok-universo-codeberg.yml@refs/heads/main'}),aud,'cortes-tiktok-universo-codeberg.yml'),'consumer');
for(const payload of [{iss:'https://evil.example/api/actions'},{aud:'wrong'},{repository:'hacker/runner'},
  {ref:'refs/heads/dev'},{event_name:'pull_request'},{exp:now-1},
  {workflow_ref:repo+'/.forgejo/workflows/cortes-tiktok-universo-codeberg.yml@refs/heads/main'}]){
  assert.equal(await second(signed(payload),aud,'cortes-tiktok-lucas4-codeberg.yml'),'');
}
const forged=signed();forged.headers.authorization+='tampered';
assert.equal(await second(forged,aud,'cortes-tiktok-lucas4-codeberg.yml'),'');
console.log('CODEBERG_SCOPED_OIDC_TESTS_PASS=1');
