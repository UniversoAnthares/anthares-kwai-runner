import {verify,createPublicKey} from "node:crypto";
import {constants} from "node:fs";
import {readFile,access} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import {dirname,join,resolve} from "node:path";
import os from "node:os";
import http from "node:http";
export const DEVICE="ANTHARES-HOSTINGER";
export const PATH="/anthares-independent/status.php";
export function authorized(input,publicKey,now=Date.now()) {
  if(input?.method!=="GET" || input.path!==PATH || input.query || input.body || input.signer!=="anthares-remote-mcp")return false;
  if(!/^[0-9]{13}$/.test(input.timestamp||"") || Math.abs(now-Number(input.timestamp))>30000)return false;
  if(!/^[A-Za-z0-9_-]{86}$/.test(input.signature||""))return false;
  try {
    const key=createPublicKey(publicKey);
    if(key.asymmetricKeyType!=="ed25519")return false;
    const data=Buffer.from(input.timestamp+"\nGET\n"+PATH+"\n");
    return verify(null,data,key,Buffer.from(input.signature,"base64url"));
  }catch{return false;}
}
async function gatewayHealth(socketPath) {
  if(typeof socketPath!=="string" || !socketPath.startsWith("/"))return false;
  return new Promise(resolve=>{
    let done=false;
    const finish=v=>{if(!done){done=true;resolve(v)}};
    const req=http.get({socketPath,path:"/api/health",timeout:2500},res=>{
      let body="";res.on("data",b=>{body+=b;if(body.length>16384){req.destroy();finish(false)}});
      res.on("end",()=>{try{const d=JSON.parse(body);finish(res.statusCode===200&&(d.ok===true||d.status==="ok"))}catch{finish(false)}});
    });
    req.on("timeout",()=>{req.destroy();finish(false)});req.on("error",()=>finish(false));
  });
}
export async function snapshot(config) {
  if(config.executor_id!==DEVICE)throw new Error("invalid_config");
  let kilo=false;try{await access(config.kilo_binary,constants.X_OK);kilo=true}catch{}
  return {ok:true,provider:"hostinger",executor_id:DEVICE,read_only:true,
    supported_operations:["system_info","session_status","capabilities"],observed_at:new Date().toISOString(),
    runtime:{node:process.version,platform:os.platform(),arch:os.arch()},
    host_observations:{cpu_threads:os.cpus().length,total_host_memory_bytes:os.totalmem(),
      note:"Shared-host observations; not the account CPU/RAM/storage allowance."},
    services:{gateway_reachable:await gatewayHealth(config.gateway_socket),kilo_cli_executable:kilo},
    inference:"not_tested",capacity_limits:"not_verified"};
}
export async function handle(input,config,{now=Date.now(),collect=snapshot}={}) {
  if(!authorized(input,config.public_key,now))return {_http_status:401,error:"unauthorized"};
  return {_http_status:200,...await collect(config)};
}
async function main() {
  let raw="";for await(const chunk of process.stdin){raw+=chunk;if(raw.length>4096)throw new Error("oversized_input")}
  const config=JSON.parse(await readFile(join(dirname(fileURLToPath(import.meta.url)),"config.json"),"utf8"));
  const out=await handle(JSON.parse(raw),config);process.stdout.write(JSON.stringify(out));
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  main().catch(()=>{process.stdout.write(JSON.stringify({_http_status:503,error:"service_unavailable"}));process.exitCode=1});
}
