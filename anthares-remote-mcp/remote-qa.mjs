import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const port=3197;
const token='ara-remote-qa-client-token-0123456789-abcdefghijklmnopqrstuvwxyz';
const child=spawn(process.execPath,['remote-server.mjs'],{cwd:new URL('.',import.meta.url),env:{...process.env,ARA_INTERNAL_MCP_PORT:String(port),ARA_MCP_CLIENT_TOKEN:token,ANTHARES_CONTROL_URL:'https://anthares-remote-control.onrender.com'},stdio:['ignore','pipe','pipe']});
let stderr='';child.stderr.on('data',c=>{stderr+=c.toString();});
async function ready(){for(let i=0;i<50;i++){try{const r=await fetch(`http://127.0.0.1:${port}/health`);if(r.ok)return;}catch{}await sleep(100);}throw new Error(`remote MCP did not start: ${stderr}`);}
const required=['session_status','system_info','capabilities','remote_exec','process_list','clipboard_get','clipboard_set','screenshot','file_stat','file_list','file_read','file_write','file_read_chunk','file_write_chunk','remote_job_start','remote_job_list','remote_job_status','remote_job_logs','remote_job_cancel','process_start','process_kill','service_status','service_start','service_stop','file_mkdir','file_remove','file_rename','file_copy','file_sha256','file_write_atomic'];
try{
  await ready();
  const denied=await fetch(`http://127.0.0.1:${port}/mcp`,{method:'POST'});if(denied.status!==401)throw new Error(`unauthenticated expected 401 got ${denied.status}`);
  const transport=new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`),{requestInit:{headers:{Authorization:`Bearer ${token}`}}});
  const client=new Client({name:'ara-remote-qa',version:'1.0.0'});await client.connect(transport);const listed=await client.listTools();const names=new Set(listed.tools.map(t=>t.name));
  for(const name of required)if(!names.has(name))throw new Error(`missing tool ${name}`);
  if(names.size!==30)throw new Error(`expected exactly 30 tools, got ${names.size}`);
  await client.close();console.log(JSON.stringify({ok:true,tests:3,tool_count:names.size},null,2));
}finally{child.kill('SIGTERM');}
