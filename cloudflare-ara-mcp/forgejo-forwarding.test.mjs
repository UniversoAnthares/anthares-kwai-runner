import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = (await readFile(new URL('./src/index.js', import.meta.url), 'utf8'))
  .replace('import { DurableObject } from "cloudflare:workers";', 'class DurableObject {}')
  .replace(/from "\.\/([^"]+\.mjs)"/g, (_, name) => 'from "'+new URL('./src/'+name, import.meta.url).href+'"');
const runtime = await import('data:text/javascript;base64,' + Buffer.from(source + '\nexport { st };').toString('base64'));
const keys = (await import('node:crypto')).generateKeyPairSync('ed25519');
const env = {
  ARA_OAUTH_SECRET: Buffer.alloc(48, 17).toString('base64url'),
  ARA_SIGNING_PRIVATE_JWK: JSON.stringify(keys.privateKey.export({format:'jwk'})),
  ARA_SIGNING_PUBLIC_JWK: JSON.stringify(keys.publicKey.export({format:'jwk'})),
  FORGEJO_BASE_URL: 'https://example.test/forgejo'
};
globalThis.fetch = async (url) => Response.json({ ok: true, url });
const origin = 'https://anthares-ara-mcp.anthares1.workers.dev';
const token = await runtime.st(env).signToken({typ:'access',iss:origin,aud:origin,exp:Math.floor(Date.now()/1000)+60,scp:['forgejo.read','github.read']});
const res = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list',params:{}})}),env);
const list = (await res.json()).result.tools.map(t=>t.name);
assert(list.includes('forgejo_version'));
assert(list.includes('github_get_file'));
const callRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/call',params:{name:'forgejo_version',arguments:{}}})}),env);
const callJson = await callRes.json();
assert.equal(callJson.result.isError, undefined);
console.log('FORGEJO_FORWARDING_OK');
