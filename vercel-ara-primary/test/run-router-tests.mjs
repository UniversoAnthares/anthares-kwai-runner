#!/usr/bin/env node
// Runner dos testes de unidade do router.mjs (vercel-ara-primary).
//
// Este projeto Vercel depende de `pg`, `@modelcontextprotocol/sdk` e `zod`.
// Os testes nao usam Neon nem a SDK real: instalam stubs locais em
// node_modules/ para que `import { Pool } from 'pg'` resolva para um stub
// em memoria, e executam o arquivo de teste.
//
// Uso:  node vercel-ara-primary/test/run-router-tests.mjs
//
// Nao requer rede. Nao modifica nenhum arquivo versionado.

import { mkdirSync, writeFileSync, copyFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const here = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(here, '..');
const nm = join(projectRoot, 'node_modules');

function writeStub(relPath, content) {
  const target = join(nm, relPath);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content, 'utf8');
}

console.log('[runner] preparando stubs de teste em node_modules/ ...');

// --- pg ---
writeStub('pg/package.json', JSON.stringify({ name: 'pg', version: '8.16.3', type: 'module', exports: { '.': './index.mjs' } }));
copyFileSync(join(here, 'pg-stub.mjs'), join(nm, 'pg', 'index.mjs'));

// --- @modelcontextprotocol/sdk ---
writeStub('@modelcontextprotocol/sdk/package.json', JSON.stringify({
  name: '@modelcontextprotocol/sdk', version: '1.18.2', type: 'module',
  exports: { '.': './index.mjs', './server/mcp.js': './server/mcp.js', './server/streamableHttp.js': './server/streamableHttp.js' },
}));
writeStub('@modelcontextprotocol/sdk/index.mjs', 'export { };\n');
writeStub('@modelcontextprotocol/sdk/server/mcp.js', `import { setGlobalServer } from './streamableHttp.js';
export class McpServer {
  constructor(opts) { this.opts = opts; this._tools = new Map(); }
  registerTool(name, desc, handler) { this._tools.set(name, { desc, handler }); }
  async connect(transport) { this._transport = transport; setGlobalServer(this); }
}
`);
writeStub('@modelcontextprotocol/sdk/server/streamableHttp.js', `let globalServer = null;
export class StreamableHTTPServerTransport {
  constructor(opts) { this.opts = opts; }
  async handleRequest(req, res, rpc) {
    const tool = rpc && rpc.method === 'tools/call' ? rpc.params?.name : null;
    const args = rpc && rpc.params ? rpc.params.arguments : {};
    if (!tool) { res.statusCode = 400; res.end(JSON.stringify({ error: 'bad_request' })); return; }
    if (res.writableEnded) return;
    if (globalServer && globalServer._tools && globalServer._tools.has(tool)) {
      const entry = globalServer._tools.get(tool);
      try {
        const result = await entry.handler(args);
        if (res.writableEnded) return;
        if (result && result.content) res.end(JSON.stringify(result));
        else res.end(JSON.stringify({ content: [{ type: 'text', text: typeof result === 'string' ? result : JSON.stringify(result) }] }));
      } catch (e) {
        if (res.writableEnded) return;
        res.statusCode = 500;
        res.end(JSON.stringify({ error: e.message }));
      }
    } else {
      if (res.writableEnded) return;
      res.statusCode = 501;
      res.end(JSON.stringify({ error: 'not_implemented_via_transport' }));
    }
  }
  async close() { }
}
export function setGlobalServer(server) { globalServer = server; }
`);

// --- zod ---
writeStub('zod/package.json', JSON.stringify({ name: 'zod', version: '3.25.76', type: 'module', exports: { '.': './index.mjs' } }));
writeStub('zod/index.mjs', `function makeStringSchema(opts = {}) {
  return {
    _type: 'zod_string',
    min(n) { return makeStringSchema({ ...opts, min: n }); },
    max(n) { return makeStringSchema({ ...opts, max: n }); },
    default(v) { return makeStringSchema({ ...opts, default: v }); },
    optional() { return makeStringSchema({ ...opts, optional: true }); },
    ...opts,
  };
}
function makeNumberSchema(opts = {}) {
  return {
    _type: 'zod_number',
    int() { return makeNumberSchema({ ...opts, int: true }); },
    min(n) { return makeNumberSchema({ ...opts, min: n }); },
    max(n) { return makeNumberSchema({ ...opts, max: n }); },
    default(v) { return makeNumberSchema({ ...opts, default: v }); },
    optional() { return makeNumberSchema({ ...opts, optional: true }); },
    ...opts,
  };
}
function makeBooleanSchema(opts = {}) {
  return { _type: 'zod_boolean', default(v) { return makeBooleanSchema({ ...opts, default: v }); }, ...opts };
}
function makeArraySchema(item, opts = {}) {
  return { _type: 'zod_array', item, max(n) { return makeArraySchema(item, { ...opts, max: n }); }, default(v) { return makeArraySchema(item, { ...opts, default: v }); }, ...opts };
}
export const z = {
  string: (opts = {}) => makeStringSchema(opts),
  number: (opts = {}) => makeNumberSchema(opts),
  boolean: (opts = {}) => makeBooleanSchema(opts),
  array: (item, opts = {}) => makeArraySchema(item, opts),
  enum: (opts) => ({ _type: 'zod_enum', opts }),
  object: (shape) => ({ _type: 'zod_object', shape }),
};
`);

const testFile = join(projectRoot, 'api', 'router.test.mjs');
if (!existsSync(testFile)) {
  console.error('[runner] arquivo de teste nao encontrado:', testFile);
  process.exit(2);
}

console.log('[runner] executando', testFile);
const res = spawnSync(process.execPath, [testFile], { stdio: 'inherit' });
process.exit(res.status ?? 1);
