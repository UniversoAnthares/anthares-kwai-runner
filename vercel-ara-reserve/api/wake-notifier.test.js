'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {notifyWakeAfterCommit,SIGNAL_URL,DEVICE}=require('./wake-notifier');
const goodSecret='PUBLISHER_TOKEN_TEST_ONLY_0123456789abcdefghijklmnopqrstuvwxyz';
const env={ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:goodSecret};
test('off by default does not access network',async()=>{
 let called=false;const r=await notifyWakeAfterCommit(DEVICE,{env:{},fetchImpl:async()=>{called=true}});
 assert.equal(r.reason,'disabled');assert.equal(called,false);
});
test('fails closed on missing/invalid key',async()=>{
 for(const secret of [undefined,'short',' '.repeat(64),'x'.repeat(30)+'\n']){
  let called=false;const r=await notifyWakeAfterCommit(DEVICE,{env:{ARA_WAKE_NOTIFY_ENABLED:'1',ARA_WAKE_NOTIFY_SECRET:secret},fetchImpl:async()=>{called=true}});
  assert.equal(r.reason,'unconfigured');assert.equal(called,false);
 }
});
test('wrong device never publishes',async()=>{
 let called=false;const r=await notifyWakeAfterCommit('OTHER',{env,fetchImpl:async()=>{called=true}});
 assert.equal(r.reason,'other_device');assert.equal(called,false);
});
test('202 receipt records sequence and sends only device identity',async()=>{
 let seen={};const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async(url,opts)=>{
  seen={url,opts};return{status:202,json:async()=>({ok:true,sequence:17})};
 }});
 assert.deepEqual(r,{enabled:true,ok:true,reason:'broker_recorded',sequence:17});
 assert.equal(seen.url,SIGNAL_URL);assert.equal(seen.opts.method,'POST');assert.equal(seen.opts.redirect,'error');
 assert.deepEqual(JSON.parse(seen.opts.body),{device_id:DEVICE});
 assert.equal(seen.opts.headers.Authorization,'Bearer '+goodSecret);
 assert.match(seen.opts.headers['User-Agent'],/AntharesARA-Wake/);
 assert.doesNotMatch(seen.opts.body,/job|args|secret|token|command/);
});
test('202 without sequence remains accepted without false sequence proof',async()=>{
 const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>({status:202,json:async()=>({ok:true})})});
 assert.deepEqual(r,{enabled:true,ok:true,reason:'broker_accepted'});
});
test('non-202 response returns diagnostic without throwing',async()=>{
 for(const code of [200,400,401,403,409,429,503]){
  const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>({status:code})});
  assert.equal(r.ok,false);assert.equal(r.reason,'http_'+code);
 }
});
test('transport exceptions and timeouts are fail-open to caller',async()=>{
 const r=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>{throw Error('unavailable')}});
 assert.equal(r.reason,'transport_error');
 const t=await notifyWakeAfterCommit(DEVICE,{env,fetchImpl:async()=>{throw Object.assign(Error('timeout'),{name:'TimeoutError'})}});
 assert.equal(t.reason,'timeout');
});


test('HTTPS direct origin uses custom lookup with original hostname and bearer',async()=>{
  const {EventEmitter}=require('node:events');
  let captured={};
  const requestImpl=(url,opts,done)=>{
    captured={url,opts};
    const req=new EventEmitter();
    req.end=body=>{
      captured.body=body;
      const res=new EventEmitter();
      res.statusCode=202;
      queueMicrotask(()=>{
        done(res);
        res.emit('data',Buffer.from('{"ok":true,"protocol":"ara-wake-v1","sequence":29}'));
        res.emit('end');
      });
    };
    req.destroy=e=>req.emit('error',e);
    return req;
  };
  const result=await notifyWakeAfterCommit(DEVICE,{
    env:{...env,ARA_WAKE_ORIGIN_IP:'203.0.113.10'},requestImpl,
    fetchImpl:async()=>{throw Error('public CDN fetch must not be used');}
  });
  assert.deepEqual(result,{enabled:true,ok:true,reason:'broker_recorded',sequence:29});
  assert.equal(captured.url,SIGNAL_URL);
  assert.equal(captured.opts.method,'POST');
  assert.equal(captured.opts.agent,false);
  assert.equal(captured.opts.headers.Authorization,'Bearer '+goodSecret);
  assert.equal(captured.opts.headers['Content-Length'],Buffer.byteLength(captured.body));
  assert.deepEqual(JSON.parse(captured.body),{device_id:DEVICE});
  await new Promise(resolve=>captured.opts.lookup('anthares.us',{all:false},(error,address,family)=>{
    assert.equal(error,null);assert.equal(address,'203.0.113.10');assert.equal(family,4);resolve();
  }));
  await new Promise(resolve=>captured.opts.lookup('anthares.us',{all:true},(error,addresses)=>{
    assert.equal(error,null);assert.deepEqual(addresses,[{address:'203.0.113.10',family:4}]);resolve();
  }));
});
test('invalid direct origin is rejected before networking',async()=>{
  for(const invalid of ['127.0.0.1','10.0.0.2','192.168.1.2','not-an-ip']){
    let used=false;
    const r=await notifyWakeAfterCommit(DEVICE,{
      env:{...env,ARA_WAKE_ORIGIN_IP:invalid},
      requestImpl:()=>{used=true;throw Error('should not call');},
      fetchImpl:async()=>{used=true;throw Error('should not call');}
    });
    assert.equal(r.reason,'invalid_origin');assert.equal(used,false);
  }
});
test('direct origin non-202 response fails open',async()=>{
  const {EventEmitter}=require('node:events');
  const requestImpl=(url,opts,done)=>{
    const req=new EventEmitter();
    req.end=()=>{
      const res=new EventEmitter();res.statusCode=403;
      queueMicrotask(()=>{done(res);res.emit('data',Buffer.from('blocked'));res.emit('end');});
    };
    req.destroy=e=>req.emit('error',e);
    return req;
  };
  const r=await notifyWakeAfterCommit(DEVICE,{env:{...env,ARA_WAKE_ORIGIN_IP:'203.0.113.10'},requestImpl});
  assert.equal(r.ok,false);assert.equal(r.reason,'http_403');
});
