import { test } from 'node:test';
import assert from 'node:assert';
import crypto from 'node:crypto';

process.env.ARA_PUBLIC_ORIGIN = 'https://anthares-remote-mcp-primary.vercel.app';
process.env.ARA_OAUTH_TOKEN_SECRET = '0123456789012345678901234567890123456789012345678901234567890123';
process.env.ARA_CONTROL_PRIVATE_KEY_B64 = '';

function makeToken(scopes) {
  const secret = process.env.ARA_OAUTH_TOKEN_SECRET;
  assert.ok(secret, 'TOKEN_SECRET deve estar definido');
  const now = Math.floor(Date.now() / 1000);
  const body = Buffer.from(JSON.stringify({
    typ: 'access', iss: 'https://anthares-remote-mcp-primary.vercel.app', aud: 'https://anthares-remote-mcp-primary.vercel.app',
    sub: 'anthares-owner', cid: 'test-client', scp: scopes,
    iat: now, exp: now + 900, jti: 'test-jti-1234',
  })).toString('base64url');
  const sig = crypto.createHmac('sha256', secret).update(body).digest('base64url');
  return `${body}.${sig}`;
}

function makeReq(method, route, headers = {}, body = null) {
  return {
    method, url: `https://test.local/${route}`, query: route ? { route } : {},
    headers: { 'content-type': 'application/json', ...headers },
    body: body === null ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)),
  };
}

function makeRes() {
  const chunks = [];
  const headers = {};
  let statusCode = 200;
  let writableEnded = false;
  const listeners = {};
  return {
    get statusCode() { return statusCode; },
    set statusCode(v) { statusCode = v; },
    setHeader(k, v) { headers[k] = v; },
    write(chunk) { chunks.push(chunk); },
    end(chunk) { if (chunk) chunks.push(chunk); writableEnded = true; },
    get _body() { return Buffer.concat(chunks.map(c => Buffer.from(c))).toString(); },
    get _headers() { return headers; },
    get _statusCode() { return statusCode; },
    get writableEnded() { return writableEnded; },
    on(event, cb) { if (!listeners[event]) listeners[event] = []; listeners[event].push(cb); },
    emit(event, ...args) { if (listeners[event]) listeners[event].forEach(cb => cb(...args)); },
  };
}

const { default: handler } = await import('./router.mjs');

test('handler retorna 401 sem token de acesso', async () => {
  const req = makeReq('POST', 'mcp', {}, { method: 'tools/call', params: { name: 'remote_job_start', arguments: {} } });
  const res = makeRes();
  await handler(req, res);
  assert.strictEqual(res._statusCode, 401);
  const body = JSON.parse(res._body);
  assert.strictEqual(body.error, 'unauthorized');
});

test('shell retorna 403 tool_blocked para qualquer token', async () => {
  const token = makeToken(['ara.read', 'ara.write', 'ara.exec']);
  const req = makeReq('POST', 'mcp', { authorization: `Bearer ${token}` }, {
    method: 'tools/call', params: { name: 'shell', arguments: { command: 'echo hi' } },
  });
  const res = makeRes();
  await handler(req, res);
  assert.strictEqual(res._statusCode, 403);
  const body = JSON.parse(res._body);
  assert.strictEqual(body.error, 'tool_blocked');
  assert.strictEqual(body.tool, 'shell');
});

test('remote_job_start retorna 403 sem escopo ara.exec no token', async () => {
  const token = makeToken(['ara.read', 'ara.write']);
  const req = makeReq('POST', 'mcp', { authorization: `Bearer ${token}` }, {
    method: 'tools/call', params: { name: 'remote_job_start', arguments: { command_id: 'git.status', args: [] } },
  });
  const res = makeRes();
  await handler(req, res);
  assert.strictEqual(res._statusCode, 403);
  const body = JSON.parse(res._body);
  assert.strictEqual(body.error, 'insufficient_scope');
  assert.strictEqual(body.required_scope, 'ara.exec');
});

test('remote_job_start com ara.exec no token nao retorna insufficient_scope', async () => {
  const token = makeToken(['ara.read', 'ara.write', 'ara.exec']);
  const req = makeReq('POST', 'mcp', { authorization: `Bearer ${token}` }, {
    method: 'tools/call', params: { name: 'remote_job_start', arguments: { command_id: 'git.status', args: [], timeout_seconds: 30 } },
  });
  const res = makeRes();
  await handler(req, res);
  const body = JSON.parse(res._body);
  assert.notStrictEqual(body.error, 'insufficient_scope', 'escopo ara.exec deve ser aceito pelo token');
});

test('todas as BLOCKED_TOOLS retornam 403', async () => {
  const blocked = ['shell','process_start','process_kill','service_start','service_stop','clipboard_set','file_write','file_write_chunk','file_write_atomic','file_mkdir','file_remove','file_rename','file_copy','job_start','job_cancel','remote_exec'];
  const token = makeToken(['ara.read', 'ara.write', 'ara.exec']);
  for (const tool of blocked) {
    const req = makeReq('POST', 'mcp', { authorization: `Bearer ${token}` }, {
      method: 'tools/call', params: { name: tool, arguments: {} },
    });
    const res = makeRes();
    await handler(req, res);
    const body = JSON.parse(res._body);
    assert.strictEqual(res._statusCode, 403, `${tool} deve retornar 403`);
    assert.strictEqual(body.error, 'tool_blocked', `${tool} error`);
    assert.strictEqual(body.tool, tool, `${tool} tool name`);
  }
});

test('escopo forjado no corpo nao substitui escopo do token', async () => {
  const token = makeToken(['ara.read']);
  const req = makeReq('POST', 'mcp', { authorization: `Bearer ${token}` }, {
    method: 'tools/call', params: { name: 'remote_job_start', arguments: { command_id: 'git.status', args: [], scope: 'ara.exec' } },
  });
  const res = makeRes();
  await handler(req, res);
  assert.strictEqual(res._statusCode, 403);
  const body = JSON.parse(res._body);
  assert.strictEqual(body.error, 'insufficient_scope');
});

console.log('Todos os testes de unidade do router passaram.');
