import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {readFileSync} from 'node:fs';
import {kwaiPersistentCloudIdentity,localBlockedByCloudCutover,
        persistentCloudEnabled} from './kwai-persistent-cloud-identity.mjs';

const TOKEN=Buffer.alloc(32,31).toString('base64url');
const HASH=crypto.createHash('sha256').update(TOKEN).digest('hex');
const env={KWAI_PERSISTENT_CLOUD_PUBLISH_ENABLED:'1',
           KWAI_PERSISTENT_CLOUD_TOKEN_SHA256:HASH};
const request=(token=TOKEN,method='POST')=>({
 method,headers:new Headers({Authorization:'Bearer '+token}),
});
test('credential is absent and route stays disabled by default',()=>{
 assert.equal(kwaiPersistentCloudIdentity(request(),'kwai-lease',{}),null);
 assert.equal(kwaiPersistentCloudIdentity(request(),'kwai-lease',
   {KWAI_PERSISTENT_CLOUD_TOKEN_SHA256:HASH}),null);
 assert.equal(persistentCloudEnabled({}),false);
 assert.equal(localBlockedByCloudCutover({role:'kwai-physical'},'kwai-start',{}),false);
});
test('only separately configured 256-bit token authorizes persistent Android',()=>{
 const actor=kwaiPersistentCloudIdentity(request(),'kwai-lease',env);
 assert.equal(actor?.role,'kwai-persistent-cloud');
 assert.equal(actor?.workflow,'cloud:android:redroid');
 for(const bad of ['',TOKEN.slice(0,42)+'A','not-a-token',TOKEN+'x']){
   assert.equal(kwaiPersistentCloudIdentity(request(bad),'kwai-lease',env),null);
 }
 assert.equal(kwaiPersistentCloudIdentity(request(),'kwai-lease',
   {...env,KWAI_PERSISTENT_CLOUD_TOKEN_SHA256:'invalid'}),null);
 assert.equal(kwaiPersistentCloudIdentity(request(TOKEN,'GET'),'kwai-lease',env),null);
});
test('new identity has no producer, probe, browser or admin actions',()=>{
 for(const action of ['enqueue','kwai-physical-repair-no-post','kwai-unproven',
                      'probe','buffer-post','browser-open','kwai-physical-stats']){
   assert.equal(kwaiPersistentCloudIdentity(request(),action,env),null);
 }
 for(const action of ['kwai-lease','kwai-renew','kwai-start','kwai-confirm','kwai-fail'])
   assert.equal(kwaiPersistentCloudIdentity(request(),action,env)?.role,
     'kwai-persistent-cloud');
});
test('cutover stops NEW physical/mobile work, preserves existing completion',()=>{
 for(const role of ['kwai-physical','kwai-mobile','kwai-mobile-primary']){
   for(const action of ['kwai-lease','kwai-start'])
      assert.equal(localBlockedByCloudCutover({role},action,env),true);
   for(const action of ['kwai-renew','kwai-confirm','kwai-fail'])
      assert.equal(localBlockedByCloudCutover({role},action,env),false);
   assert.equal(localBlockedByCloudCutover({role},'kwai-start',{}),false);
 }
 assert.equal(localBlockedByCloudCutover({role:'kwai-persistent-cloud'},'kwai-lease',env),false);
});
test('both canonical account handlers and HTTP entry route the same gated role',()=>{
 const src=readFileSync(new URL('./index.mjs',import.meta.url),'utf8');
 assert.match(src,/kwaiPersistentCloudIdentity\(request,action\)/);
 assert.equal(src.split("const persistentCloud=actor.role==='kwai-persistent-cloud'").length-1,2);
 assert.equal(src.split('if(localBlockedByCloudCutover(actor,action))').length-1,2);
 assert.equal(src.split("!cloud&&!mobile&&!persistentCloud").length-1,1);
 assert.equal(src.split("!cloud&&!mobilePrimary&&!persistentCloud").length-1,1);
 assert.match(src,/async function kwaiSecondaryAction\(/);
 assert.match(src,/async function kwaiAction\(/);
});
