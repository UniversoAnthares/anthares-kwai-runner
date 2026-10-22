import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const files=[
  'infra/neon-cortes-tiktok/index.mjs',
  'infra/neon-cortes-lucasrosalem4/index.mjs',
];
const RUNNER='UniversoAnthares/anthares-kwai-runner';
const AUDIENCE='https://anthares-remote-primary.vercel.app/api/cortes-tiktok';
const ISSUER='https://codeberg.org/api/actions';
const WORKFLOW=RUNNER+'/.forgejo/workflows/tiktok-codeberg-primary.yml@refs/heads/main';
const keypair=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
const jwk={...keypair.publicKey.export({format:'jwk'}),kid:'codeberg-oidc-test',alg:'RS256',kty:'RSA'};
const encode=obj=>Buffer.from(JSON.stringify(obj)).toString('base64url');
const identity=()=>({
  iss:ISSUER,aud:AUDIENCE,sub:'repo:'+RUNNER+':ref:refs/heads/main',
  repository:RUNNER,repository_id:'2708613',
  ref:'refs/heads/main',workflow_ref:WORKFLOW,
  event_name:'workflow_dispatch',
  iat:Math.floor(Date.now()/1000)-20,
  exp:Math.floor(Date.now()/1000)+240,
  nbf:Math.floor(Date.now()/1000)-30,
});
function mint(payload,corrupt=false){
  const unsigned=encode({alg:'RS256',kid:jwk.kid,typ:'JWT'})+'.'+encode(payload);
  const signature=crypto.sign('RSA-SHA256',Buffer.from(unsigned),keypair.privateKey).toString('base64url');
  return unsigned+'.'+(corrupt?'ZmFrZQ':signature);
}
function harness(path){
  const src=fs.readFileSync(path,'utf8');
  const begin=src.indexOf('const FORGEJO_ISSUER=');
  const end=src.indexOf('async function schema(){',begin);
  assert.ok(begin>0&&end>begin,'Codeberg OIDC verifier exists');
  const context=vm.createContext({
    Buffer,crypto,RUNNER,AUDIENCE,token:req=>req.jwt,
    AbortSignal:{timeout:()=>new AbortController().signal},
    fetch:async url=>{
      if(url===ISSUER+'/.well-known/openid-configuration')
        return {ok:true,json:async()=>({issuer:ISSUER,jwks_uri:ISSUER+'/.well-known/keys'})};
      if(url===ISSUER+'/.well-known/keys')
        return {ok:true,json:async()=>({keys:[jwk]})};
      throw Error('unsupported fetch');
    }
  });
  vm.runInContext(src.slice(begin,end)+'\nthis.check=codebergRole;',context,{filename:path});
  return context.check;
}
for(const file of files){
  test(file+' authenticates signed exact Codeberg workflow',async()=>{
    const check=harness(file);
    assert.equal(await check({jwt:mint(identity())}),'consumer');
  });
  for(const [label,change] of Object.entries({
    'wrong repository':{repository:'hacker/repo'},
    'different immutable repo id':{repository_id:'999'},
    'incorrect branch':{ref:'refs/heads/dev'},
    'untrusted workflow':{workflow_ref:RUNNER+'/.forgejo/workflows/other.yml@refs/heads/main'},
    'bad issuer':{iss:'https://other.example/api/actions'},
    'incorrect audience':{aud:'https://other.example'},
    'pull request event':{event_name:'pull_request'},
    'expired token':{exp:Math.floor(Date.now()/1000)-2},
    'foreign subject':{sub:'repo:other/repo:ref:refs/heads/main'},
  })){
    test(file+' blocks '+label,async()=>{
      const check=harness(file);
      assert.equal(await check({jwt:mint({...identity(),...change})}),'');
    });
  }
  test(file+' blocks invalid RSA signature',async()=>{
    assert.equal(await harness(file)({jwt:mint(identity(),true)}),'');
  });
}
test('Codeberg workflow never publishes on dispatch smoke',()=>{
 const yaml=fs.readFileSync('.forgejo/workflows/tiktok-codeberg-primary.yml','utf8');
 assert.match(yaml,/enable-openid-connect:\s*true/);
 assert.match(yaml,/TIKTOK_CODEBERG_PREFLIGHT_ONLY:/);
 assert.match(yaml,/vars\.TIKTOK_CODEBERG_PRIMARY/);
 assert.match(yaml,/persist-credentials:\s*false/);
 assert.doesNotMatch(yaml,/ARA_SHARED:\s*\$\{/);
});
