import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const port = 3117;
const token = 'qa-client-token-0123456789-abcdefghijklmnopqrstuvwxyz';
const control = 'qa-control-token-0123456789-abcdefghijklmnopqrstuvwxyz';
const base = `http://127.0.0.1:${port}`;
const child = spawn(process.execPath, ['server.mjs'], {
  cwd: new URL('.', import.meta.url),
  env: {
    ...process.env,
    PORT: String(port),
    ARA_MCP_TRANSPORT: 'http',
    ARA_MCP_CLIENT_TOKEN: token,
    ARA_SHARED: control,
    ANTHARES_CONTROL_URL: 'http://127.0.0.1:9',
  },
  stdio: ['ignore', 'pipe', 'pipe'],
});

let stderr = '';
child.stderr.on('data', c => { stderr += c.toString(); });

async function waitReady() {
  for (let i = 0; i < 50; i++) {
    try {
      const r = await fetch(`${base}/health`);
      if (r.status === 200) return;
    } catch {}
    await sleep(100);
  }
  throw new Error(`server did not start: ${stderr}`);
}

function assert(ok, message) {
  if (!ok) throw new Error(message);
}

try {
  await waitReady();

  const health = await fetch(`${base}/health`);
  const healthBody = await health.json();
  assert(health.status === 200 && healthBody.ok === true && healthBody.auth === 'configured', 'health/auth readiness failed');

  const unauth = await fetch(`${base}/mcp`, { method: 'POST' });
  assert(unauth.status === 401, `unauthenticated MCP expected 401, got ${unauth.status}`);

  const bad = await fetch(`${base}/mcp`, {
    method: 'POST',
    headers: { Authorization: 'Bearer definitely-wrong-token' },
  });
  assert(bad.status === 401, `invalid token expected 401, got ${bad.status}`);

  const transport = new StreamableHTTPClientTransport(new URL(`${base}/mcp`), {
    requestInit: { headers: { Authorization: `Bearer ${token}` } },
  });
  const client = new Client({ name: 'ara-qa', version: '1.0.0' });
  await client.connect(transport);
  const listed = await client.listTools();
  const byName = new Map(listed.tools.map(t => [t.name, t]));
  const required = [
    'session_status','system_info','capabilities','remote_exec','process_list',
    'process_start','process_kill','service_status','service_start','service_stop',
    'clipboard_get','clipboard_set','screenshot','file_stat','file_list','file_read',
    'file_write','file_read_chunk','file_write_chunk','file_mkdir','file_remove',
    'file_rename','file_copy','file_sha256','file_write_atomic','remote_job_start',
    'remote_job_list','remote_job_status','remote_job_logs','remote_job_cancel'
  ];
  for (const name of required) assert(byName.has(name), `missing MCP tool ${name}`);
  assert(byName.size >= 30, `expected at least 30 tools, got ${byName.size}`);

  const processStart = byName.get('process_start');
  assert(processStart?.inputSchema?.properties?.args?.type === 'array', 'process_start.args must be an array');
  const remove = byName.get('file_remove');
  assert(remove?.inputSchema?.properties?.recursive?.type === 'boolean', 'file_remove.recursive must be boolean');
  await client.close();

  console.log(JSON.stringify({ ok: true, tests: 7, tool_count: byName.size, tools: [...byName.keys()].sort() }, null, 2));
} finally {
  child.kill('SIGTERM');
}
