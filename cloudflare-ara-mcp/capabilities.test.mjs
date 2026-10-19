import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { generateKeyPairSync, verify } from 'node:crypto';

const source = (await readFile(new URL('./src/index.js', import.meta.url), 'utf8'))
  .replace('import { DurableObject } from "cloudflare:workers";', 'class DurableObject {}')
  .replace(/from "\.\/([^"]+\.mjs)"/g, (_, name) => 'from "'+new URL('./src/'+name,import.meta.url).href+'"');
const runtime = await import('data:text/javascript;base64,' + Buffer.from(source + '\nexport { callTool };').toString('base64'));
const keys = generateKeyPairSync('ed25519');
const env = {
  ARA_OAUTH_SECRET: Buffer.alloc(48, 17).toString('base64url'),
  ARA_SIGNING_PRIVATE_JWK: JSON.stringify(keys.privateKey.export({format:'jwk'})),
  ARA_SIGNING_PUBLIC_JWK: JSON.stringify(keys.publicKey.export({format:'jwk'}))
};
let calls = [];
globalThis.fetch = async (url, init) => {
  calls.push(url);
  assert.equal(new URL(url).pathname, '/v1/mcp/status');
  const timestamp = init.headers['x-ara-timestamp'];
  const target = new URL(url);
  assert(verify(null, Buffer.from(`${timestamp}\nGET\n${target.pathname}${target.search}\n`), keys.publicKey, Buffer.from(init.headers['x-ara-signature'], 'base64url')));
  return Response.json({ backend:'vercel-neon', connected:true });
};
const result = JSON.parse((await runtime.callTool(env, 'capabilities')).content[0].text);
assert.equal(result.ok, true);
assert.equal(result.device_connected, true);
assert(result.capabilities.includes('shell'));
assert.equal(calls.length, 1);
const denied = await runtime.default.fetch(new Request('https://anthares-ara-mcp.anthares1.workers.dev/mcp', {method:'POST',body:'{}'}), env);
assert.equal(denied.status, 401);
globalThis.fetch = async () => Response.json({error:'unauthorized'}, {status:401});
await assert.rejects(runtime.callTool(env, 'capabilities'), /control 401/);
console.log('PASS capabilities verifies signed backend, reports supported contract, rejects unauthorized control and unauthenticated MCP');
