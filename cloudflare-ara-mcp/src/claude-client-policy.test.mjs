import test from 'node:test';
import assert from 'node:assert/strict';
import {
  CLAUDE_CALLBACK, CLAUDE_CLIENT_IDS, isClaudeClient,
  isClaudeRedirect, isClaudeCallbackPair, permittedClaudeScopes
} from './claude-client-policy.mjs';
test('known Claude client IDs only', () => {
  for (const id of CLAUDE_CLIENT_IDS) {
    assert.equal(isClaudeClient(id), true);
    assert.equal(isClaudeCallbackPair(id, CLAUDE_CALLBACK), true);
  }
  for (const id of ['https://claude.ai.evil.example/oauth/mcp-oauth-client-metadata',
    'https://attacker.example/client.json', 'https://chatgpt.com/oauth/client.json',
    'https://claude.ai/oauth/mcp-oauth-client-metadata/extra', '']) {
    assert.equal(isClaudeClient(id), false);
  }
});
test('exact Claude OAuth redirect only', () => {
  for (const uri of ['https://attacker.example/api/mcp/auth_callback',
    'https://claude.ai.evil.example/api/mcp/auth_callback',
    'https://claude.ai/api/mcp/auth_callback/',
    'http://claude.ai/api/mcp/auth_callback']) {
    assert.equal(isClaudeRedirect(uri), false);
    assert.equal(isClaudeCallbackPair(CLAUDE_CLIENT_IDS[0], uri), false);
  }
});
test('Claude OAuth grants GitHub branch tools while keeping remote control read-only', () => {
  for (const scopes of [['ara.read'], ['github.read'], ['github.write'],
    ['ara.read','github.read','github.write']])
    assert.equal(permittedClaudeScopes(scopes), true);
  for (const scopes of [[], ['ara.write'], ['ara.read','ara.write'],
    ['github.write','ara.write'], ['admin']])
    assert.equal(permittedClaudeScopes(scopes), false);
});
