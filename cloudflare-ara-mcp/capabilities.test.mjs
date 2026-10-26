import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { generateKeyPairSync, verify } from 'node:crypto';

const source = (await readFile(new URL('./src/index.js', import.meta.url), 'utf8'))
  .replace('import { DurableObject } from "cloudflare:workers";', 'class DurableObject {}')
  .replace(/from "\.\/([^"]+\.mjs)"/g, (_, name) => 'from "'+new URL('./src/'+name,import.meta.url).href+'"');
const runtime = await import('data:text/javascript;base64,' + Buffer.from(source + '\nexport { callTool, st };').toString('base64'));
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
assert.equal(result.client_access.remote_execution, 'not_granted');
assert.equal(result.client_access.discovery_command, undefined);
assert.deepEqual(result.mcp_connector.delegated_tools, []);

async function rpc(scopes, method, params = {}) {
  const origin = 'https://anthares-ara-mcp.anthares1.workers.dev';
  // Fixture-only signed tokens, with independent read/write grants; no owner OAuth.
  const token = await runtime.st(env).signToken({typ:'access',iss:origin,aud:origin,
    exp:Math.floor(Date.now()/1000)+60,scp:scopes});
  const response = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',
    headers:{authorization:'Bearer '+token,'content-type':'application/json'},
    body:JSON.stringify({jsonrpc:'2.0',id:1,method,params})}),env);
  return response.json();
}
const readonly = ['ara.read'];
const writable = ['ara.read','ara.write'];
const init = await rpc(writable, 'initialize');
assert.equal(init.result.serverInfo.version,'1.2.0');
assert.match(init.result.instructions,/Call capabilities/);
assert.match(init.result.instructions,/security denials/);
const readTools = (await rpc(readonly,'tools/list')).result.tools;
assert(!readTools.some(t=>t.name==='remote_exec'));
assert(readTools.some(t=>t.name==='file_read'));
const blocked = await rpc(readonly,'tools/call',{name:'remote_exec',arguments:{command:'NEVER_EXECUTE'}});
assert.equal(blocked.error.message,'insufficient_scope');
const readCaps = JSON.parse((await rpc(readonly,'tools/call',{name:'capabilities'})).result.content[0].text);
assert.equal(readCaps.client_access.remote_execution,'not_granted');
assert.equal(readCaps.client_access.discovery_command,undefined);
const writeCaps = JSON.parse((await rpc(writable,'tools/call',{name:'capabilities'})).result.content[0].text);
assert.equal(writeCaps.client_access.remote_execution,'granted');
assert.match(writeCaps.client_access.discovery_command,/AntharesBrowserHub.ps1/);
assert.match(writeCaps.client_access.discovery_command,/bridge.py/);
assert.match(writeCaps.client_access.discovery_command,/Invoke-AntharesAgent.ps1/);
assert.deepEqual(writeCaps.mcp_connector.delegated_tools,[]);
const githubCaps = JSON.parse((await rpc(['ara.read','github.read','github.write'],'tools/call',{name:'capabilities'})).result.content[0].text);
assert.equal(githubCaps.mcp_connector.delegated_tools.length,3);
assert.equal(githubCaps.client_access.remote_execution,'not_granted');
const session = JSON.parse((await rpc(writable,'tools/call',{name:'session_status'})).result.content[0].text);
assert.equal(session.connected,true);
assert.equal(session.client_access.revision,'2026-10-26.1');
assert.equal(session.client_access.remote_execution,'granted');
// Capability discovery must never execute a shell or touch clipboard/file data.
assert(calls.every(url=>new URL(url).pathname==='/v1/mcp/status'));
const denied = await runtime.default.fetch(new Request('https://anthares-ara-mcp.anthares1.workers.dev/mcp', {method:'POST',body:'{}'}), env);
assert.equal(denied.status, 401);
globalThis.fetch = async () => Response.json({error:'unauthorized'}, {status:401});
await assert.rejects(runtime.callTool(env, 'capabilities'), /control 401/);
console.log('PASS authenticated discovery: initialize, scope-aware capabilities/session status, read-only shell denial, signed backend, no shell side effects, anonymous 401');
