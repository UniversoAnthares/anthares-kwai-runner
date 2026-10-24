// Owner-authorized Kilo enrollment. Exact official metadata and loopback callback.
export const KILO_CLIENT_ID = 'https://kilo.ai/docs/oauth/kilo/client.json';
export const KILO_CALLBACK = 'http://127.0.0.1:19876/mcp/oauth/callback';
export function isKiloClient(id) { return id === KILO_CLIENT_ID; }
export function isKiloCallbackPair(id, uri) {
  return isKiloClient(id) && uri === KILO_CALLBACK;
}
export function isKiloResource(id, resource, origin) {
  return isKiloClient(id) && (resource === origin || resource === origin + '/');
}
