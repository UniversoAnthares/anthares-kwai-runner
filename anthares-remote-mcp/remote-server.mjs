import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createServer } from 'node:http';
import { randomUUID, timingSafeEqual } from 'node:crypto';
import { z } from 'zod';
import { controlFailoverOrigins, signedControlFetch } from './control-client.mjs';
import { servicePublicKey } from './service-signing.mjs';
import { registerExtendedTools } from './extended-tools.mjs';

const CONTROL_URL = (process.env.ANTHARES_CONTROL_URL || 'https://anthares-ara-control.onrender.com').replace(/\/$/, '');
const DEFAULT_DEVICE = process.env.ANTHARES_DEVICE_ID || 'DESKTOP-FTDK0HP';
const CLIENT_TOKEN = process.env.ARA_MCP_CLIENT_TOKEN || '';

async function api(path, { method='GET', body, timeoutMs=140000 }={}) {
  const res = await signedControlFetch(CONTROL_URL, path, { method, body, timeoutMs });
  const raw = await res.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch { data = { raw }; }
  if (!res.ok) throw new Error(`control ${res.status}: ${data.error || data.raw || 'request failed'}`);
  return data;
}

async function execute(type, args={}, timeoutSeconds=30, deviceId=DEFAULT_DEVICE) {
  const idempotencyKey = `mcp-${randomUUID()}`;
  return api('/v1/mcp/execute', {
    method:'POST',
    timeoutMs:Math.min(150000,(timeoutSeconds+12)*1000),
    body:{device_id:deviceId,type,args,timeout_seconds:timeoutSeconds,idempotency_key:idempotencyKey}
  });
}

function text(value) {
  return { content:[{type:'text',text:typeof value==='string'?value:JSON.stringify(value,null,2)}] };
}

function createMcpServer() {
  const server = new McpServer({name:'Anthares Remote',version:'0.8.0'});

  server.registerTool('session_status',{description:'Check the Anthares Remote Agent heartbeat for the authorized Windows device.',inputSchema:{device_id:z.string().default(DEFAULT_DEVICE)}},async({device_id})=>text(await api(`/v1/mcp/status?device_id=${encodeURIComponent(device_id)}`)));
  server.registerTool('system_info',{description:'Return OS, CPU, RAM, GPU and disk information.',inputSchema:{device_id:z.string().default(DEFAULT_DEVICE)}},async({device_id})=>text(await execute('system_info',{},30,device_id)));
  server.registerTool('remote_exec',{description:'Execute a PowerShell or CMD command on the authorized Windows device.',inputSchema:{command:z.string().min(1),shell:z.enum(['powershell','cmd']).default('powershell'),timeout_seconds:z.number().int().min(1).max(120).default(30),device_id:z.string().default(DEFAULT_DEVICE)}},async({command,shell,timeout_seconds,device_id})=>text(await execute('shell',{command,shell},timeout_seconds,device_id)));
  server.registerTool('process_list',{description:'List running processes.',inputSchema:{device_id:z.string().default(DEFAULT_DEVICE)}},async({device_id})=>text(await execute('process_list',{},30,device_id)));
  server.registerTool('clipboard_get',{description:'Read text from the interactive desktop clipboard.',inputSchema:{device_id:z.string().default(DEFAULT_DEVICE)}},async({device_id})=>text(await execute('clipboard_get',{},20,device_id)));
  server.registerTool('clipboard_set',{description:'Set text on the interactive desktop clipboard.',inputSchema:{text:z.string(),device_id:z.string().default(DEFAULT_DEVICE)}},async({text:value,device_id})=>text(await execute('clipboard_set',{text:value},20,deviceId=device_id)));
  server.registerTool('screenshot',{description:'Capture a JPEG screenshot.',inputSchema:{display:z.string().default('0'),device_id:z.string().default(DEFAULT_DEVICE)}},async({display,device_id})=>{const out=await execute('screenshot',{display},45,device_id);return {content:[{type:'image',data:out.output||'',mimeType:'image/jpeg'}]};});
  server.registerTool('file_stat',{description:'Stat a file or directory inside allowlisted roots.',inputSchema:{path:z.string(),device_id:z.string().default(DEFAULT_DEVICE)}},async({path,device_id})=>text(await execute('file_stat',{path},30,device_id)));
  server.registerTool('file_list',{description:'List a directory inside allowlisted roots.',inputSchema:{path:z.string(),device_id:z.string().default(DEFAULT_DEVICE)}},async({path,device_id})=>text(await execute('file_list',{path},30,device_id)));
  server.registerTool('file_read',{description:'Read a file up to 1 MiB and return base64.',inputSchema:{path:z.string(),device_id:z.string().default(DEFAULT_DEVICE)}},async({path,device_id})=>text(await execute('file_read',{path},30,device_id)));
  server.registerTool('file_write',{description:'Write a file up to 1 MiB from base64.',inputSchema:{path:z.string(),base64:z.string(),device_id:z.string().default(DEFAULT_DEVICE)}},async({path,base64,device_id})=>text(await execute('file_write',{path,base64},30,device_id)));
  server.registerTool('file_read_chunk',{description:'Read a chunk of a larger file.',inputSchema:{path:z.string(),offset:z.number().int().min(0).default(0),length:z.number().int().min(1).max(524288).default(524288),device_id:z.string().default(DEFAULT_DEVICE)}},async({path,offset,length,device_id})=>text(await execute('file_read_chunk',{path,offset:String(offset),length:String(length)},40,device_id)));
  server.registerTool('file_write_chunk',{description:'Write a base64 chunk to a larger file.',inputSchema:{path:z.string(),offset:z.number().int().min(0),base64:z.string(),truncate:z.boolean().default(false),device_id:z.string().default(DEFAULT_DEVICE)}},async({path,offset,base64,truncate,device_id})=>text(await execute('file_write_chunk',{path,offset:String(offset),base64,truncate:truncate?'1':'0'},40,device_id)));
  server.registerTool('remote_job_start',{description:'Start a detached background command.',inputSchema:{command:z.string().min(1),name:z.string().default(''),device_id:z.string().default(DEFAULT_DEVICE)}},async({command,name,device_id})=>text(await execute('job_start',{command,name},30,device_id)));
  server.registerTool('remote_job_list',{description:'List detached jobs.',inputSchema:{limit:z.number().int().min(1).max(100).default(20),include_command:z.boolean().default(false),device_id:z.string().default(DEFAULT_DEVICE)}},async({limit,include_command,device_id})=>text(await execute('job_list',{limit:String(limit),include_command:include_command?'1':'0'},30,device_id)));
  server.registerTool('remote_job_status',{description:'Get detached job status.',inputSchema:{job_id:z.string(),include_command:z.boolean().default(false),device_id:z.string().default(DEFAULT_DEVICE)}},async({job_id,include_command,device_id})=>text(await execute('job_status',{job_id,include_command:include_command?'1':'0'},30,device_id)));
  server.registerTool('remote_job_logs',{description:'Read detached job logs.',inputSchema:{job_id:z.string(),offset_bytes:z.number().int().min(0).optional(),max_bytes:z.number().int().min(1).max(262144).default(262144),tail_lines:z.number().int().min(1).max(5000).default(200),device_id:z.string().default(DEFAULT_DEVICE)}},async({job_id,offset_bytes,max_bytes,tail_lines,device_id})=>text(await execute('job_logs',{job_id,offset_bytes:offset_bytes===undefined?'':String(offset_bytes),max_bytes:String(max_bytes),tail_lines:String(tail_lines)},30,device_id)));
  server.registerTool('remote_job_cancel',{description:'Terminate a detached job process tree.',inputSchema:{job_id:z.string(),device_id:z.string().default(DEFAULT_DEVICE)}},async({job_id,device_id})=>text(await execute('job_cancel',{job_id},30,device_id)));
  server.registerTool('capabilities',{description:'List capabilities exposed by the signed ARA control bridge.',inputSchema:{}},async()=>text(await api('/v1/mcp/capabilities')));

  registerExtendedTools(server,{execute,text,defaultDevice:DEFAULT_DEVICE});
  return server;
}

function validToken(header) {
  if (CLIENT_TOKEN.length < 32) return false;
  const expected=Buffer.from('Bearer '+CLIENT_TOKEN); const actual=Buffer.from(header||'');
  return actual.length===expected.length && timingSafeEqual(actual,expected);
}

const http=createServer(async(req,res)=>{
  if(req.method==='GET' && req.url==='/health'){
    res.writeHead(CLIENT_TOKEN.length>=32?200:503,{'Content-Type':'application/json','Cache-Control':'no-store'});
    res.end(JSON.stringify({ok:CLIENT_TOKEN.length>=32,service:'anthares-remote-signed-mcp',auth:'ed25519-control',preferred_control:CONTROL_URL,controls:controlFailoverOrigins}));return;
  }
  if(req.method==='GET' && req.url==='/control-key'){
    res.writeHead(200,{'Content-Type':'application/x-pem-file','Cache-Control':'no-store'});res.end(servicePublicKey());return;
  }
  if(req.url!=='/mcp'){res.writeHead(404);res.end();return;}
  if(req.method!=='POST'){res.writeHead(405,{Allow:'POST'});res.end();return;}
  if(!validToken(req.headers.authorization)){res.writeHead(401,{'WWW-Authenticate':'Bearer','Content-Type':'application/json'});res.end(JSON.stringify({error:'unauthorized'}));return;}
  try{
    const transport=new StreamableHTTPServerTransport({sessionIdGenerator:undefined});
    const instance=createMcpServer();
    await instance.connect(transport);
    await transport.handleRequest(req,res);
    res.on('close',()=>transport.close().catch(()=>{}));
  }catch(e){if(!res.headersSent){res.writeHead(500,{'Content-Type':'application/json'});res.end(JSON.stringify({error:'mcp_request_failed'}));}}
});
http.requestTimeout=150000;
console.log(`Signed ARA MCP preferred_control=${CONTROL_URL} failover=${controlFailoverOrigins.join(',')}`);
http.listen(Number(process.env.ARA_INTERNAL_MCP_PORT||3118),'127.0.0.1',()=>console.log('Signed ARA MCP internal server ready'));
