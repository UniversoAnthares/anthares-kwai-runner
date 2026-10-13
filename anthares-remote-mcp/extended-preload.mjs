import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { registerExtendedTools } from './extended-tools.mjs';

const CONTROL_URL = (process.env.ANTHARES_CONTROL_URL || 'https://anthares-remote-control.onrender.com').replace(/\/$/, '');
const CONTROL_TOKEN = process.env.ARA_SHARED || '';
const DEFAULT_DEVICE = process.env.ANTHARES_DEVICE_ID || 'DESKTOP-FTDK0HP';
const registered = new WeakSet();

async function api(path, { method = 'GET', body, timeoutMs = 140000 } = {}) {
  if (!CONTROL_TOKEN) throw new Error('ARA_SHARED is not configured');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${CONTROL_URL}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${CONTROL_TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'AntharesRemoteMCP/0.3',
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const raw = await res.text();
    let data;
    try { data = raw ? JSON.parse(raw) : {}; } catch { data = { raw }; }
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

const originalConnect = McpServer.prototype.connect;
McpServer.prototype.connect = async function patchedConnect(transport) {
  if (!registered.has(this)) {
    registerExtendedTools(this, { execute, text, defaultDevice: DEFAULT_DEVICE });
    registered.add(this);
  }
  return originalConnect.call(this, transport);
};
