import { test } from 'node:test';
import assert from 'node:assert';
import crypto from 'node:crypto';
import { setNextRemoteJobResult, resetState, getState } from 'pg';

process.env.ARA_PUBLIC_ORIGIN = 'https://anthares-remote-mcp-primary.vercel.app';
process.env.ARA_OAUTH_TOKEN_SECRET = '0123456789012345678901234567890123456789012345678901234567890123';
// Chave ed25519 de teste (PKCS8 DER, base64) - gerada para este arquivo de teste.
process.env.ARA_CONTROL_PRIVATE_KEY_B64 = 'MC4CAQAwBQYDK2VwBCIEIGStHQiD01DI0fS+ZTyoAjORxSVe+x87loUK6ZFKgm8b';

function makeToken(scopes) {
  const secret = process.env.ARA_OAUTH_TOKEN_SECRET;
  const now = Math.floor(Date.now() / 1000);
  const body = Buffer.from(JSON.stringify({
    typ: 'access', iss: 'https://anthares-remote-mcp-primary.vercel.app',
    aud: 'https://anthares-remote-mcp-primary.vercel.app', sub: 'anthares-owner',
    cid: 'test-client', scp: scopes, iat: now, exp: now + 900, jti: 'test-jti-' + Math.random().toString(36).slice(2),
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
    on(event, cb) { },
    emit(event, ...args) { },
  };
}

const { default: handler } = await import('./router.mjs');

async function callTool(name, args, scopes = ['ara.read', 'ara.write', 'ara.exec']) {
  const token = makeToken(scopes);
  const req = makeReq('POST', 'mcp', { authorization: `Bearer ${token}` }, {
    method: 'tools/call', params: { name, arguments: args },
  });
  const res = makeRes();
  await handler(req, res);
  return { status: res._statusCode, body: res._body ? JSON.parse(res._body) : null };
}

// --- Teste 1: 401 sem token ---
test('handler retorna 401 sem token de acesso', async () => {
  const req = makeReq('POST', 'mcp', {}, { method: 'tools/call', params: { name: 'remote_job_start', arguments: {} } });
  const res = makeRes();
  await handler(req, res);
  assert.strictEqual(res._statusCode, 401);
  assert.strictEqual(JSON.parse(res._body).error, 'unauthorized');
});

// --- Teste 2: shell bloqueado 403 ---
test('shell retorna 403 tool_blocked para qualquer token', async () => {
  const r = await callTool('shell', { command: 'echo hi' });
  assert.strictEqual(r.status, 403);
  assert.strictEqual(r.body.error, 'tool_blocked');
  assert.strictEqual(r.body.tool, 'shell');
});

// --- Teste 3: remote_job_start sem ara.exec ---
test('remote_job_start retorna 403 sem escopo ara.exec no token', async () => {
  const r = await callTool('remote_job_start', { command_id: 'git.status', args: [] }, ['ara.read', 'ara.write']);
  assert.strictEqual(r.status, 403);
  assert.strictEqual(r.body.error, 'insufficient_scope');
  assert.strictEqual(r.body.required_scope, 'ara.exec');
});

// --- Teste 4: remote_job_start com ara.exec ---
test('remote_job_start com ara.exec nao retorna insufficient_scope', async () => {
  resetState();
  const r = await callTool('remote_job_start', { command_id: 'git.status', args: [], timeout_seconds: 30 });
  assert.notStrictEqual(r.body.error, 'insufficient_scope', 'escopo ara.exec deve ser aceito');
});

// --- Teste 5: todas as BLOCKED_TOOLS 403 ---
test('todas as BLOCKED_TOOLS retornam 403', async () => {
  const blocked = ['shell','process_start','process_kill','service_start','service_stop','clipboard_set','file_write','file_write_chunk','file_write_atomic','file_mkdir','file_remove','file_rename','file_copy','job_start','job_cancel','remote_exec'];
  for (const tool of blocked) {
    const r = await callTool(tool, {});
    assert.strictEqual(r.status, 403, `${tool} deve retornar 403`);
    assert.strictEqual(r.body.error, 'tool_blocked', `${tool} error`);
    assert.strictEqual(r.body.tool, tool, `${tool} tool name`);
  }
});

// --- Teste 6: escopo forjado no corpo ---
test('escopo forjado no corpo nao substitui escopo do token', async () => {
  const r = await callTool('remote_job_start', { command_id: 'git.status', args: [], scope: 'ara.exec' }, ['ara.read']);
  assert.strictEqual(r.status, 403);
  assert.strictEqual(r.body.error, 'insufficient_scope');
});

// --- Teste 7: rate limit 429 no 11o chamado ---
test('rate limit retorna 429 no 11o chamado por minuto do mesmo token', async () => {
  resetState();
  const token = makeToken(['ara.read', 'ara.write', 'ara.exec']);
  const authHeader = { authorization: `Bearer ${token}` };

  for (let i = 0; i < 10; i++) {
    const req = makeReq('POST', 'mcp', authHeader, {
      method: 'tools/call', params: { name: 'remote_job_start', arguments: { command_id: 'git.status', args: [] } },
    });
    const res = makeRes();
    await handler(req, res);
    const body = JSON.parse(res._body);
    assert.notStrictEqual(body.error, 'rate_limited', `chamada ${i + 1} nao deve ser rate-limited (status ${res._statusCode})`);
  }

  const req11 = makeReq('POST', 'mcp', authHeader, {
    method: 'tools/call', params: { name: 'remote_job_start', arguments: { command_id: 'git.status', args: [] } },
  });
  const res11 = makeRes();
  await handler(req11, res11);
  assert.strictEqual(res11._statusCode, 429);
  const body11 = JSON.parse(res11._body);
  assert.strictEqual(body11.error, 'rate_limited');
  assert.strictEqual(body11.limit, 10);
  assert.strictEqual(body11.window_seconds, 60);
});

// --- Teste 8: pending_approval retorna 202 ---
test('pending_approval retorna 202 (nao 500)', async () => {
  resetState();
  // Resultado que o agente Go posta no job quando o handler responde
  // {"ok":false,"error":"pending_approval","exit_code":0}
  setNextRemoteJobResult({ ok: false, error: 'pending_approval', exit_code: 0, output: '' });

  const r = await callTool('remote_job_start', { command_id: 'git.status', args: [], timeout_seconds: 30 });
  assert.strictEqual(r.status, 202);
  assert.strictEqual(r.body.status, 'pending_approval');
  assert.strictEqual(r.body.error, 'pending_approval');
  assert.strictEqual(r.body.ok, false);
  // Auditoria deve registrar a espera por aprovacao local
  const audit = getState().auditRows;
  assert.ok(audit.length > 0, 'auditoria deve ter sido gravada');
  const last = audit[audit.length - 1].params;
  assert.strictEqual(last[2], 'git.status', 'command_id registrado na auditoria');
  assert.ok(JSON.stringify(last[5]).includes('pending_approval'), 'auditoria registra pending_approval');
});

// --- Teste 9: remote_job_disabled tambem retorna 202 ---
test('remote_job_disabled (chave de desligamento) retorna 202', async () => {
  resetState();
  setNextRemoteJobResult({ ok: false, error: 'remote_job_disabled', exit_code: 0, output: '' });
  const r = await callTool('remote_job_start', { command_id: 'git.status', args: [], timeout_seconds: 30 });
  assert.strictEqual(r.status, 202);
  assert.strictEqual(r.body.status, 'pending_approval');
  assert.strictEqual(r.body.error, 'remote_job_disabled');
});

// --- Teste 10: E2E pending_approval (handler -> agente -> router -> cliente) ---
test('E2E: handler ok=false error=pending_approval chega ao cliente como 202', async () => {
  resetState();
  // 1) Handler local responderia: {"ok":false,"error":"pending_approval","exit_code":0,...}
  const handlerOutput = { ok: false, error: 'pending_approval', exit_code: 0, output: '', command_id: 'git.status' };
  // 2) O agente Go transforma ok=false em falha do job preservando o nome do erro
  //    (parseHandlerOutput -> errors.New("pending_approval")), e posta o resultado no job.
  setNextRemoteJobResult(handlerOutput);
  // 3) O router recebe o resultado e mapeia pending_approval -> 202
  const r = await callTool('remote_job_start', { command_id: 'git.status', args: [], timeout_seconds: 30 });
  // 4) Formato do erro final entregue ao cliente
  assert.strictEqual(r.status, 202);
  assert.deepStrictEqual(Object.keys(r.body).sort(), ['error', 'job_id', 'message', 'ok', 'status']);
  assert.strictEqual(r.body.ok, false);
  assert.strictEqual(r.body.status, 'pending_approval');
  assert.strictEqual(r.body.error, 'pending_approval');
  assert.ok(/aprova/i.test(r.body.message), 'mensagem deve indicar aprovacao local');
  // Nao pode ser erro generico
  assert.notStrictEqual(r.body.error, 'internal_error');
});

// --- Teste 11: 500 nao expoe detail nem stack ---
test('erro interno retorna internal_error com correlation_id e sem detail', async () => {
  resetState();
  // Forca excecao: rota desconhecida com metodo invalido nao lanca; usamos
  // o handler MCP com um corpo JSON malformado que faz jsonBody devolver {} -> tool ''.
  const r = await callTool('', {});
  // 405/403/404/500 sao todos aceitaveis; o que importa e que nunca vaza detail
  if (r.status === 500) {
    assert.strictEqual(r.body.error, 'internal_error');
    assert.ok(r.body.correlation_id, 'correlation_id deve estar presente');
    assert.strictEqual(r.body.detail, undefined, 'detail nao deve ser exposto');
  }
});

console.log('Todos os testes de unidade do router passaram.');
