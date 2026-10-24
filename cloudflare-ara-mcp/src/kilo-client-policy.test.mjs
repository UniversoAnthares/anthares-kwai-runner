import test from 'node:test';
import assert from 'node:assert/strict';
import {KILO_CLIENT_ID, KILO_CALLBACK, isKiloClient, isKiloCallbackPair, isKiloResource} from './kilo-client-policy.mjs';
test('only exact Kilo metadata and callback are enrolled', () => {
  assert(isKiloCallbackPair(KILO_CLIENT_ID, KILO_CALLBACK));
  for (const id of [KILO_CLIENT_ID+'/', KILO_CLIENT_ID+'?x=1', 'https://kilo.ai.evil.test/docs/oauth/kilo/client.json', 'https://evil.test/client.json'])
    assert.equal(isKiloClient(id), false);
  for (const uri of [KILO_CALLBACK+'/', KILO_CALLBACK+'?x=1', KILO_CALLBACK.replace('19876','19877'), KILO_CALLBACK.replace('127.0.0.1','localhost'), KILO_CALLBACK.replace('127.0.0.1','evil.test')])
    assert.equal(isKiloCallbackPair(KILO_CLIENT_ID, uri), false);
});
test('root slash interoperability does not admit other resources or clients', () => {
  const origin='https://anthares-ara-mcp.anthares1.workers.dev';
  assert(isKiloResource(KILO_CLIENT_ID, origin+'/', origin));
  for (const resource of [origin+'/mcp', origin+'//', origin+'/?x=1', 'https://evil.test/'])
    assert.equal(isKiloResource(KILO_CLIENT_ID, resource, origin), false);
  assert.equal(isKiloResource('https://evil.test/client.json', origin+'/', origin), false);
});
