import {authorized,synchronize,latest} from '../lib/mirror.mjs';
export default async function handler(req,res){
 res.setHeader('Cache-Control','no-store');res.setHeader('Content-Type','application/json');
 if(!authorized(req.headers.authorization,process.env.CRON_SECRET)){res.statusCode=401;return res.end(JSON.stringify({ok:false,error:'unauthorized'}));}
 if(!['POST','GET'].includes(req.method)){res.statusCode=405;return res.end(JSON.stringify({ok:false,error:'method_not_allowed'}));}
 try{
  const body=typeof req.body==='string'?JSON.parse(req.body||'{}'):(req.body||{});
  const ref=body.ref||req.query?.ref||'main';
  if(req.query?.status==='1'){res.statusCode=200;return res.end(JSON.stringify(await latest({ref})));}
  const type=String(req.headers['x-mirror-trigger']||((req.headers['user-agent']||'').includes('vercel-cron')?'vercel-daily':'manual'));
  const result=await synchronize({ref,fault:body.fault||'',trigger:{type,scheduled_time:req.headers['x-mirror-scheduled-time']||null}});
  console.log(JSON.stringify({service:'wordpress-mirror',run_id:result.run_id,ok:result.ok,ref:result.ref,outcome:result.outcome,error:result.error}));
  res.statusCode=result.ok?200:result.error==='LOCK_BUSY'?409:502;return res.end(JSON.stringify(result));
 }catch(error){res.statusCode=400;return res.end(JSON.stringify({ok:false,error:String(error.code||'REQUEST_FAILED')}));}
}
