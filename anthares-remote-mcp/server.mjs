import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const CONTROL_URL = (process.env.ANTHARES_CONTROL_URL || 'https://anthares-x-render-worker-v3.onrender.com').replace(/\/$/, '');
const CONTROL_TOKEN = process.env.ARA_SHARED || '';
const DEFAULT_DEVICE = process.env.ANTHARES_DEVICE_ID || 'DESKTOP-FTDK0HP';

if (!CONTROL_TOKEN) {
  console.error('ARA_SHARED is required');
  process.exit(2);
}

async function api(path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${CONTROL_URL}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${CONTROL_TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'AntharesRemoteMCP/0.1',
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await res.text();
    let data;
    try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
    if (!res.ok) throw new Error(`control ${res.status}: ${data.error || data.raw || 'request failed'}`);
    return data;
  } finally {
    clearTimeout(timer);
  }
}

async function execute(type, args = {}, timeoutSeconds = 30, deviceId = DEFAULT_DEVICE) {
  return api('/v1/control/execute', {
    method: 'POST',
    timeoutMs: Math.min(150000, (timeoutSeconds + 12) * 1000),
    body: { device_id: deviceId, type, args, timeout_seconds: timeoutSeconds },
  });
}

function text(value) {
  return { content: [{ type: 'text', text: typeof value === 'string' ? value : JSON.stringify(value, null, 2) }] };
}

const server = new McpServer({ name: 'Anthares Remote', version: '0.1.0' });

server.registerTool('session_status', {
  description: 'Check the Anthares Remote Agent heartbeat for a Windows device.',
  inputSchema: { device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ device_id }) => text(await api(`/v1/control/status?device_id=${encodeURIComponent(device_id)}`)));

server.registerTool('system_info', {
  description: 'Return OS, CPU, RAM and GPU information from the remote device.',
  inputSchema: { device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ device_id }) => text(await execute('system_info', {}, 30, device_id)));

server.registerTool('remote_exec', {
  description: 'Execute a PowerShell or CMD command on the authorized remote Windows device.',
  inputSchema: {
    command: z.string().min(1),
    shell: z.enum(['powershell', 'cmd']).default('powershell'),
    timeout_seconds: z.number().int().min(1).max(120).default(30),
    device_id: z.string().default(DEFAULT_DEVICE),
  },
}, async ({ command, shell, timeout_seconds, device_id }) => text(await execute('shell', { command, shell }, timeout_seconds, device_id)));

server.registerTool('process_list', {
  description: 'List running processes on the remote Windows device.',
  inputSchema: { device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ device_id }) => text(await execute('process_list', {}, 30, device_id)));

server.registerTool('clipboard_get', {
  description: 'Read text from the interactive desktop clipboard.',
  inputSchema: { device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ device_id }) => text(await execute('clipboard_get', {}, 20, device_id)));

server.registerTool('clipboard_set', {
  description: 'Set text on the interactive desktop clipboard.',
  inputSchema: { text: z.string(), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ text: value, device_id }) => text(await execute('clipboard_set', { text: value }, 20, device_id)));

server.registerTool('screenshot', {
  description: 'Capture a JPEG screenshot of display 0, another display index, or all displays.',
  inputSchema: { display: z.string().default('0'), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ display, device_id }) => {
  const out = await execute('screenshot', { display }, 45, device_id);
  const b64 = out.output || '';
  return { content: [{ type: 'image', data: b64, mimeType: 'image/jpeg' }] };
});

server.registerTool('file_stat', {
  description: 'Stat a file or directory within the agent allowlisted roots.',
  inputSchema: { path: z.string(), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ path, device_id }) => text(await execute('file_stat', { path }, 30, device_id)));

server.registerTool('file_list', {
  description: 'List a directory within the agent allowlisted roots.',
  inputSchema: { path: z.string(), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ path, device_id }) => text(await execute('file_list', { path }, 30, device_id)));

server.registerTool('file_read', {
  description: 'Read a file up to 1 MiB and return its base64 payload.',
  inputSchema: { path: z.string(), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ path, device_id }) => text(await execute('file_read', { path }, 30, device_id)));

server.registerTool('file_write', {
  description: 'Write a file up to 1 MiB from base64 data within allowlisted roots.',
  inputSchema: { path: z.string(), base64: z.string(), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ path, base64, device_id }) => text(await execute('file_write', { path, base64 }, 30, device_id)));

server.registerTool('file_read_chunk', {
  description: 'Read a chunk of a larger file (maximum 512 KiB per chunk).',
  inputSchema: {
    path: z.string(), offset: z.number().int().min(0).default(0), length: z.number().int().min(1).max(524288).default(524288),
    device_id: z.string().default(DEFAULT_DEVICE),
  },
}, async ({ path, offset, length, device_id }) => text(await execute('file_read_chunk', { path, offset: String(offset), length: String(length) }, 40, device_id)));

server.registerTool('file_write_chunk', {
  description: 'Write a base64 chunk to a larger file (maximum 512 KiB per chunk).',
  inputSchema: {
    path: z.string(), offset: z.number().int().min(0), base64: z.string(), truncate: z.boolean().default(false),
    device_id: z.string().default(DEFAULT_DEVICE),
  },
}, async ({ path, offset, base64, truncate, device_id }) => text(await execute('file_write_chunk', { path, offset: String(offset), base64, truncate: truncate ? '1' : '0' }, 40, device_id)));

server.registerTool('remote_job_start', {
  description: 'Start a detached background command that continues after the MCP call ends.',
  inputSchema: { command: z.string().min(1), name: z.string().default(''), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ command, name, device_id }) => text(await execute('job_start', { command, name }, 30, device_id)));

server.registerTool('remote_job_list', {
  description: 'List detached jobs retained by Anthares Remote Agent.',
  inputSchema: { limit: z.number().int().min(1).max(100).default(20), include_command: z.boolean().default(false), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ limit, include_command, device_id }) => text(await execute('job_list', { limit: String(limit), include_command: include_command ? '1' : '0' }, 30, device_id)));

server.registerTool('remote_job_status', {
  description: 'Get the status of a detached job.',
  inputSchema: { job_id: z.string(), include_command: z.boolean().default(false), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ job_id, include_command, device_id }) => text(await execute('job_status', { job_id, include_command: include_command ? '1' : '0' }, 30, device_id)));

server.registerTool('remote_job_logs', {
  description: 'Read detached job logs by tail or byte offset.',
  inputSchema: {
    job_id: z.string(), offset_bytes: z.number().int().min(0).optional(), max_bytes: z.number().int().min(1).max(262144).default(262144),
    tail_lines: z.number().int().min(1).max(5000).default(200), device_id: z.string().default(DEFAULT_DEVICE),
  },
}, async ({ job_id, offset_bytes, max_bytes, tail_lines, device_id }) => text(await execute('job_logs', {
  job_id,
  offset_bytes: offset_bytes === undefined ? '' : String(offset_bytes),
  max_bytes: String(max_bytes), tail_lines: String(tail_lines),
}, 30, device_id)));

server.registerTool('remote_job_cancel', {
  description: 'Terminate a detached job process tree.',
  inputSchema: { job_id: z.string(), device_id: z.string().default(DEFAULT_DEVICE) },
}, async ({ job_id, device_id }) => text(await execute('job_cancel', { job_id }, 30, device_id)));

server.registerTool('capabilities', {
  description: 'List capabilities exposed by the Anthares Remote control plane.',
  inputSchema: {},
}, async () => text(await api('/v1/control/capabilities')));

const transport = new StdioServerTransport();
await server.connect(transport);
