import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { gitlabProducerRole } from '../infra/neon-cortes-tiktok/gitlab-oidc.mjs';

const AUDIENCE='https://anthares-remote-primary.vercel.app/api/cortes-tiktok';
const {privateKey,publicKey}=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
const jwk={...publicKey.export({format:'jwk'}),kid:'aoi02-fixture',alg:'RS256'};
const now=Math.floor(Date.now()/1000);
const valid={
  iss:'https://gitlab.com',aud:AUDIENCE,
  project_id:'87361774',project_path:'UniversoAnthares/anthares-clipper',
  sub:'project_path:UniversoAnthares/anthares-clipper:ref_type:branch:ref:main',
  ref:'main',ref_type:'branch',ref_protected:'true',pipeline_source:'web',
  iat:now-10,nbf:now-10,exp:now+240
};
function token(overrides={},key=privateKey){
 const hdr=Buffer.from(JSON.stringify({alg:'RS256',kid:'aoi02-fixture'})).toString('base64url');
 const payload=Buffer.from(JSON.stringify({...valid,...overrides})).toString('base64url');
 const sig=crypto.sign('RSA-SHA256',Buffer.from(hdr+'.'+payload),key).toString('base64url');
 return hdr+'.'+payload+'.'+sig;
}
const requests=[];
globalThis.fetch=async (url)=>{
 requests.push(String(url));
 if(url==='https://gitlab.com/.well-known/openid-configuration')
   return Response.json({jwks_uri:'https://gitlab.com/oauth/discovery/keys'});
 if(url==='https://gitlab.com/oauth/discovery/keys')
   return Response.json({keys:[jwk]});
 throw Error('unapproved fetch destination');
};
function req(jwt){return{headers:{authorization:'Bearer '+jwt}};}
test('accept signed exact protected GitLab producer only',async()=>{
 assert.equal(await gitlabProducerRole(req(token()),AUDIENCE),'producer');
 assert.deepEqual(requests,[
   'https://gitlab.com/.well-known/openid-configuration',
   'https://gitlab.com/oauth/discovery/keys'
 ]);
});
test('reject wrong project, ref, protection, audience, issuer, source or expiry',async()=>{
 const cases=[
  {project_id:'1'}, {project_path:'other/repo'},{sub:'other'},
  {ref:'feature'}, {ref_type:'tag'}, {ref_protected:'false'},
  {aud:'https://evil.example'}, {iss:'https://evil.example'},
  {pipeline_source:'merge_request_event'}, {exp:now-1},
 ];
 for(const invalid of cases)
   assert.equal(await gitlabProducerRole(req(token(invalid)),AUDIENCE),'',JSON.stringify(invalid));
});
test('reject forged signature and invalid JWT headers',async()=>{
 const other=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
 assert.equal(await gitlabProducerRole(req(token({},other.privateKey)),AUDIENCE),'');
 assert.equal(await gitlabProducerRole({headers:{authorization:'Bearer broken'}},AUDIENCE),'');
});
