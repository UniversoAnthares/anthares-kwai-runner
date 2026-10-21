// Fail-safe Threads local/cloud cutover.
// Only an explicit, live, verified cloud activation with a shared lease can
// suspend the proven local publisher. GitHub workflow success is not proof of a post.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=process.env.CORTES_THREADS_LOCAL_ROOT||'D:\\AntharsWork\\cortes-social-browser-20261020';
const activation=path.join(root,'threads-cloud-primary-activation.json');
export function decide(ack,nowMs=Date.now()){
 if(!ack||ack.enabled!==true)return {allow:true,reason:'CLOUD_NOT_ACTIVATED_LOCAL_PRIMARY'};
 if(ack.lease_authority!=='neon'||ack.verified_identity!=='universoanthares'||!ack.last_remote_post_url?.startsWith('https://www.threads.com/@universoanthares/post/'))
   return {allow:false,reason:'INVALID_CLOUD_ACTIVATION_RECONCILIATION_REQUIRED'};
 const when=Date.parse(ack.verified_at||'');
 if(!Number.isFinite(when)||when>nowMs+60000||nowMs-when>15*60000)
   return {allow:false,reason:'CLOUD_ACTIVATION_EXPIRED_RECONCILIATION_REQUIRED'};
 return {allow:false,reason:'CLOUD_PRIMARY_ACTIVE_WITH_SHARED_LEASE'};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 let ack=null;try{ack=JSON.parse(fs.readFileSync(activation,'utf8'))}catch{}
 const v=decide(ack);
 console.log('THREADS_EXECUTOR_ROLE=LOCAL_CONTINGENCY '+v.reason);
 process.exitCode=v.allow?0:20;
}