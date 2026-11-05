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
  FORGEJO_BASE_URL: 'https://anthares.us/forgejo',
  FORGEJO_READ_TOKEN: 'test-read-token-12345'
};
globalThis.fetch = async (url) => Response.json({ ok: true, url });
const origin = 'https://anthares-ara-mcp.anthares1.workers.dev';
const token = await runtime.st(env).signToken({typ:'access',iss:origin,aud:origin,exp:Math.floor(Date.now()/1000)+60,scp:['forgejo.read','github.read']});
const res = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list',params:{}})}),env);
const list = (await res.json()).result.tools.map(t=>t.name);
assert(list.includes('forgejo_version'));
assert(list.includes('forgejo_list_repos'));
assert(list.includes('forgejo_get_file'));
assert(list.includes('forgejo_list_runs'));
assert(list.includes('forgejo_get_run'));
assert(list.includes('github_get_file'));
const callRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/call',params:{name:'forgejo_version',arguments:{}}})}),env);
const callJson = await callRes.json();
assert.equal(callJson.result.isError, undefined);
// forgejo_list_repos with default allowed owner
const reposRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:3,method:'tools/call',params:{name:'forgejo_list_repos',arguments:{owner:'anthares-admin'}}})}),env);
const reposJson = await reposRes.json();
assert.equal(reposJson.result.isError, undefined);
// forgejo_list_repos with disallowed owner must be rejected
const badOwnerRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:4,method:'tools/call',params:{name:'forgejo_list_repos',arguments:{owner:'evil-owner'}}})}),env);
const badOwnerJson = await badOwnerRes.json();
assert.equal(badOwnerJson.result.isError, true);
// forgejo_get_file with allowed repo and path
const fileRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:5,method:'tools/call',params:{name:'forgejo_get_file',arguments:{repo:'anthares-admin/anthares-kwai-runner',path:'README.md'}}})}),env);
const fileJson = await fileRes.json();
assert.equal(fileJson.result.isError, undefined);
// forgejo_get_file with disallowed repo must be rejected
const badRepoRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:6,method:'tools/call',params:{name:'forgejo_get_file',arguments:{repo:'evil/repo',path:'README.md'}}})}),env);
const badRepoJson = await badRepoRes.json();
assert.equal(badRepoJson.result.isError, true);
// forgejo_get_file with path traversal must be rejected
const travRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:7,method:'tools/call',params:{name:'forgejo_get_file',arguments:{repo:'anthares-admin/anthares-kwai-runner',path:'../../etc/passwd'}}})}),env);
const travJson = await travRes.json();
assert.equal(travJson.result.isError, true);
// forgejo_get_run with valid run_id
const runRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:8,method:'tools/call',params:{name:'forgejo_get_run',arguments:{repo:'anthares-admin/anthares-kwai-runner',run_id:42}}})}),env);
const runJson = await runRes.json();
assert.equal(runJson.result.isError, undefined);
// forgejo_get_run with invalid run_id must be rejected
const badRunRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:9,method:'tools/call',params:{name:'forgejo_get_run',arguments:{repo:'anthares-admin/anthares-kwai-runner',run_id:'not-a-number'}}})}),env);
const badRunJson = await badRunRes.json();
assert.equal(badRunJson.result.isError, true);
// ref with path separator must be sanitized (slash removed)
const refRes = await runtime.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:10,method:'tools/call',params:{name:'forgejo_get_file',arguments:{repo:'anthares-admin/anthares-kwai-runner',path:'README.md',ref:'feature/branch'}}})}),env);
const refJson = await refRes.json();
assert.equal(refJson.result.isError, undefined);
// missing FORGEJO_READ_TOKEN must be rejected
const envNoToken = { ...env }; delete envNoToken.FORGEJO_READ_TOKEN;
const runtimeNoToken = await import('data:text/javascript;base64,' + Buffer.from((await readFile(new URL('./src/index.js', import.meta.url), 'utf8'))
  .replace('import { DurableObject } from "cloudflare:workers";', 'class DurableObject {}')
  .replace(/from "\.\/([^"]+\.mjs)"/g, (_, name) => 'from "'+new URL('./src/'+name, import.meta.url).href+'"') + '\nexport { st };').toString('base64'));
globalThis.fetch = async (url) => Response.json({ ok: true, url });
const tokenNoToken = await runtimeNoToken.st(envNoToken).signToken({typ:'access',iss:origin,aud:origin,exp:Math.floor(Date.now()/1000)+60,scp:['forgejo.read','github.read']});
const noTokenRes = await runtimeNoToken.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+tokenNoToken,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:11,method:'tools/call',params:{name:'forgejo_version',arguments:{}}})}),envNoToken);
const noTokenJson = await noTokenRes.json();
assert.equal(noTokenJson.result.isError, true);
// disallowed FORGEJO_BASE_URL host must be rejected
const envBadHost = { ...env, FORGEJO_BASE_URL: 'https://evil.com/forgejo' };
const runtimeBadHost = await import('data:text/javascript;base64,' + Buffer.from((await readFile(new URL('./src/index.js', import.meta.url), 'utf8'))
  .replace('import { DurableObject } from "cloudflare:workers";', 'class DurableObject {}')
  .replace(/from "\.\/([^"]+\.mjs)"/g, (_, name) => 'from "'+new URL('./src/'+name, import.meta.url).href+'"') + '\nexport { st };').toString('base64'));
globalThis.fetch = async (url) => Response.json({ ok: true, url });
const tokenBadHost = await runtimeBadHost.st(envBadHost).signToken({typ:'access',iss:origin,aud:origin,exp:Math.floor(Date.now()/1000)+60,scp:['forgejo.read','github.read']});
const badHostRes = await runtimeBadHost.default.fetch(new Request(origin+'/mcp', {method:'POST',headers:{authorization:'Bearer '+tokenBadHost,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:12,method:'tools/call',params:{name:'forgejo_version',arguments:{}}})}),envBadHost);
const badHostJson = await badHostRes.json();
assert.equal(badHostJson.result.isError, true);
console.log('FORGEJO_FORWARDING_OK');
