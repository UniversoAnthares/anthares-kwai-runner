/**
 * Claude.ai Free remote-MCP OAuth policy.
 * Exact known Anthropic client IDs and callback only; no wildcard redirect.
 * Initial Claude access is read-only. ChatGPT client pinning stays unchanged.
 */
export const CLAUDE_CALLBACK = 'https://claude.ai/api/mcp/auth_callback';
export const CLAUDE_CLIENT_IDS = Object.freeze([
  'https://claude.ai/oauth/mcp-oauth-client-metadata',
  'https://claude.ai/api/oauth/mcp-oauth-client-metadata'
]);
export function isClaudeClient(id) {
  return CLAUDE_CLIENT_IDS.includes(String(id || ''));
}
export function isClaudeRedirect(uri) {
  return String(uri || '') === CLAUDE_CALLBACK;
}
export function isClaudeCallbackPair(id, uri) {
  return isClaudeClient(id) && isClaudeRedirect(uri);
}
export function permittedClaudeScopes(scopes) {
  return Array.isArray(scopes) && scopes.length > 0 &&
    scopes.every(s => s === 'ara.read');
}
