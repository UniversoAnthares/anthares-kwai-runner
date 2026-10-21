import test from 'node:test';
import assert from 'node:assert/strict';
import { decide } from '../tools/threads_primary_gate.mjs';
const t = Date.parse('2026-10-21T14:00:00Z');
const run = (status,conclusion,created_at='2026-10-21T13:30:00Z') =>
  ({head_branch:'main',event:'schedule',status,conclusion,created_at});
test('missing cloud deployment allows existing local contingency',()=>
  assert.equal(decide({http:404},t).allow,true));
test('unknown network/auth result blocks local publication',()=>
  assert.equal(decide({http:401},t).allow,false));
test('active primary prevents local parallel execution',()=>
  assert.equal(decide({http:200,workflow_runs:[run('in_progress',null)]},t).allow,false));
test('recent successful primary prevents local parallel execution',()=>
  assert.equal(decide({http:200,workflow_runs:[run('completed','success')]},t).allow,false));
test('ambiguous failed primary never causes duplicate replay',()=>
  assert.equal(decide({http:200,workflow_runs:[run('completed','failure')]},t).allow,false));
test('stale successful primary requires shared lease reconciliation before fallback',()=>
  assert.equal(decide({http:200,workflow_runs:[run('completed','success','2026-10-20T13:30:00Z')]},t).allow,false));
test('readiness branch cannot be mistaken for real published primary',()=>
  assert.equal(decide({http:200,workflow_runs:[{...run('completed','success'),head_branch:'feature/threads-cloud-primary-20261021'}]},t).allow,true));
