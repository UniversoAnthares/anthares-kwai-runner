import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync,sign,createHmac} from "node:crypto";
import {mkdtemp,writeFile,copyFile,mkdir,rm,chmod,readFile} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {spawnSync} from "node:child_process";
import {authorized,handle,snapshot,DEVICE,PATH} from "./handler.mjs";
import {externalReadOnly,EXTERNAL_URL,EXTERNAL_DEVICE} from "../cloudflare-ara-mcp/src/external-readonly.mjs";
const key=generateKeyPairSync("ed25519");
const pub=key.publicKey.export({type:"spki",format:"pem"});
const input=(now=Date.now())=>{const timestamp=String(now);return {
 method:"GET",path:PATH,query:"",body:"",signer:"anthares-remote-mcp",timestamp,
 signature:sign(null,Buffer.from(timestamp+"\nGET\n"+PATH+"\n"),key.privateKey).toString("base64url")
}};
const fakeSnapshot={ok:true,provider:"hostinger",executor_id:DEVICE,read_only:true,
 supported_operations:["system_info","session_status","capabilities"],observed_at:"2026-10-30T00:00:00Z",
 runtime:{platform:"linux"},host_observations:{cpu_threads:1},services:{gateway_reachable:true}};
test("real Ed25519 valid request and exact freshness boundary",()=>{
 const now=Date.now(),v=input(now);assert(authorized(v,pub,now));assert(authorized(v,pub,now+30000));assert(!authorized(v,pub,now+30001));
});
for(const [field,value] of [["method","POST"],["path","/another"],["query","x=1"],["body","data"],["signer","other"],["timestamp","NaN"],["signature","x".repeat(86)]]){
 test("reject modified "+field,()=>{const v=input();v[field]=value;assert(!authorized(v,pub));});
}
test("different key fails closed",()=>assert(!authorized(input(),generateKeyPairSync("ed25519").publicKey.export({type:"spki",format:"pem"}))));
test("authorization happens before any diagnostic collection",async()=>{
 let count=0;const r=await handle({...input(),signature:"bad"},{public_key:pub},{collect:async()=>{count++;return fakeSnapshot}});
 assert.equal(r._http_status,401);assert.equal(count,0);
});
test("supported external operations use one correctly signed bounded request",async()=>{
 for(const name of ["system_info","session_status","capabilities"]){
  let count=0;const result=await externalReadOnly(name,{
   sign:async(method,path,raw)=>{assert.equal(method,"GET");assert.equal(path,PATH);assert.equal(raw,"");return input()},
   fetchImpl:async(url,opts)=>{count++;assert.equal(url,EXTERNAL_URL);assert.equal(opts.redirect,"manual");assert(opts.signal);
    const h=new Headers(opts.headers);assert(authorized({method:opts.method,path:new URL(url).pathname,
     signer:h.get("x-ara-signer"),timestamp:h.get("x-ara-timestamp"),signature:h.get("x-ara-signature")},pub));
    return Response.json(fakeSnapshot);
   }
  });assert.equal(count,1);assert.equal(result.device_id,EXTERNAL_DEVICE);assert.equal(result.read_only,true);assert.equal(result.job_execution,"not_supported");
  if(name==="session_status"){assert.equal(result.queued,null);assert.equal(result.uncertain,null);}
 }
});
for(const status of [401,403,429,503,302])test("external failure "+status+" never retries or changes route",async()=>{
 let calls=0;await assert.rejects(externalReadOnly("system_info",{sign:async()=>input(),fetchImpl:async()=>{calls++;return new Response("",{status})}}));
 assert.equal(calls,1);
});
test("unapproved external operation makes no network or signing call",async()=>{
 let calls=0;await assert.rejects(externalReadOnly("remote_exec",{sign:async()=>{calls++;return input()},fetchImpl:async()=>{calls++;return Response.json(fakeSnapshot)}}),/not_supported/);assert.equal(calls,0);
});
test("wrong upstream contract rejected",async()=>{
 await assert.rejects(externalReadOnly("capabilities",{sign:async()=>input(),fetchImpl:async()=>Response.json({...fakeSnapshot,supported_operations:["remote_exec"]})}),/invalid_contract/);
});
test("diagnostic snapshot reports executable permission and shared host limits honestly",async()=>{
 const dir=await mkdtemp(join(tmpdir(),"anthares-snapshot-"));
 try{
  const cli=join(dir,"cli");await writeFile(cli,"fixture",{mode:0o600});
  const config={executor_id:DEVICE,kilo_binary:cli,gateway_socket:join(dir,"absent.sock")};
  let d=await snapshot(config);assert.equal(d.services.kilo_cli_executable,false);assert.equal(d.services.gateway_reachable,false);
  await chmod(cli,0o700);d=await snapshot(config);assert.equal(d.services.kilo_cli_executable,true);
  assert.match(d.host_observations.note,/not the account/);assert.equal(d.inference,"not_tested");
 }finally{await rm(dir,{recursive:true,force:true});}
});
test("real PHP wrapper accepts valid signature and rejects forged or anonymous request",async()=>{
 const dir=await mkdtemp(join(tmpdir(),"anthares-php-"));const web=join(dir,"domain","public_html","anthares-independent");
 const privateDir=join(dir,"domain","anthares-secure","independent-service");
 try{
  await mkdir(web,{recursive:true});await mkdir(privateDir,{recursive:true});
  await copyFile(new URL("./status.php",import.meta.url),join(web,"status.php"));
  await copyFile(new URL("./handler.mjs",import.meta.url),join(privateDir,"handler.mjs"));
  await writeFile(join(privateDir,"config.json"),JSON.stringify({node_binary:process.execPath,public_key:pub,
    executor_id:DEVICE,kilo_binary:join(dir,"missing"),gateway_socket:join(dir,"missing.sock")}),{mode:0o600});
  const call=v=>{
   const server={REQUEST_METHOD:v?.method||"GET",REQUEST_URI:PATH,
    HTTP_X_ARA_SIGNER:v?.signer||"",HTTP_X_ARA_TIMESTAMP:v?.timestamp||"",HTTP_X_ARA_SIGNATURE:v?.signature||""};
   const bootstrap='$_SERVER=json_decode(getenv("ARA_TEST_REQUEST"),true);register_shutdown_function(function(){fwrite(STDERR,"HTTP_STATUS=".http_response_code());});require $argv[1];';
   const r=spawnSync("php",["-r",bootstrap,join(web,"status.php")],{env:{...process.env,ARA_TEST_REQUEST:JSON.stringify(server)},encoding:"utf8",timeout:10000});
   assert.equal(r.error,undefined);assert.equal(r.status,0);return {status:r.stderr.match(/HTTP_STATUS=(\d+)/)?.[1],data:JSON.parse(r.stdout)};
  };
  let r=call(input());assert.equal(r.status,"200");assert.equal(r.data.executor_id,DEVICE);assert.equal(r.data.read_only,true);
  r=call({...input(),signature:"x".repeat(86)});assert.equal(r.status,"401");assert.equal(r.data.error,"unauthorized");
  r=call();assert.equal(r.status,"401");r=call({...input(),method:"POST"});assert.equal(r.status,"405");
 }finally{await rm(dir,{recursive:true,force:true});}
});
test("OAuth MCP dispatch reaches external service; write operations never reach host or Windows queue",async()=>{
 let source=await readFile(new URL("../cloudflare-ara-mcp/src/index.js",import.meta.url),"utf8");
 source=source.replace('import { DurableObject } from "cloudflare:workers";',"class DurableObject {}")
 .replace(/from "\.\/([^"]+\.mjs)"/g,(_,name)=>'from "'+new URL("../cloudflare-ara-mcp/src/"+name,import.meta.url).href+'"');
 const worker=(await import("data:text/javascript;base64,"+Buffer.from(source).toString("base64"))).default;
 const secret=Buffer.alloc(48,71);const env={ARA_OAUTH_SECRET:secret.toString("base64url"),
  ARA_SIGNING_PRIVATE_JWK:JSON.stringify(key.privateKey.export({format:"jwk"})),
  ARA_SIGNING_PUBLIC_JWK:JSON.stringify(key.publicKey.export({format:"jwk"}))};
 const payload=Buffer.from(JSON.stringify({typ:"access",iss:"https://anthares-ara-mcp.anthares1.workers.dev",
  aud:"https://anthares-ara-mcp.anthares1.workers.dev",exp:Math.floor(Date.now()/1000)+600,
  cid:"https://chatgpt.com/oauth/client.json",scp:["ara.read","ara.write"]})).toString("base64url");
 const token=payload+"."+createHmac("sha256",secret).update(payload).digest("base64url");
 const oldFetch=globalThis.fetch;let calls=0;
 globalThis.fetch=async(url,opts)=>{
  calls++;assert.equal(url,EXTERNAL_URL);const h=new Headers(opts.headers);
  assert(authorized({method:opts.method,path:PATH,signer:h.get("x-ara-signer"),timestamp:h.get("x-ara-timestamp"),signature:h.get("x-ara-signature")},pub));
  return Response.json(fakeSnapshot);
 };
 const invoke=async name=>{const r=await worker.fetch(new Request("https://anthares-ara-mcp.anthares1.workers.dev/mcp",{
  method:"POST",headers:{authorization:"Bearer "+token},body:JSON.stringify({jsonrpc:"2.0",id:1,method:"tools/call",params:{name,arguments:{device_id:DEVICE}}})}),env);return r.json()};
 try{
  const result=await invoke("system_info");assert.equal(JSON.parse(result.result.content[0].text).device_id,DEVICE);assert.equal(calls,1);
  const denied=await invoke("remote_exec");assert.equal(denied.result.isError,true);assert.match(denied.result.content[0].text,/not_supported/);assert.equal(calls,1);
 }finally{globalThis.fetch=oldFetch;}
});
