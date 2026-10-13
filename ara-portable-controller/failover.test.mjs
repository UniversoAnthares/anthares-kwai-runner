import assert from 'node:assert/strict';
import test from 'node:test';
import {chooseController} from './failover.mjs';
const urls=['https://one.example','https://two.example','https://three.example'];
test('rejects duplicate endpoints',async()=>{await assert.rejects(()=>chooseController({origins:[urls[0],urls[0],urls[2]],deviceId:'dev',token:'test'}),/three_distinct/)});
test('fails closed when no endpoint is reachable',async()=>{const x=await chooseController({origins:urls,deviceId:'dev',token:'test',timeoutMs:200});assert.equal(x,null)});
