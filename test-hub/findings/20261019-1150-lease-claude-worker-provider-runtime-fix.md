# Claude owner callback Worker runtime correction
STATUS: RUNNING
AREA: ara-mcp-claude-deploy, claude-session
LEASE_OWNER: codex-01a14ef0
EXPIRES_UTC: 2026-10-19T12:18:00Z
SUPERSEDES: 20261019-1147-lease-claude-owner-window-renew.md
BASELINE_PROVEN: production13f5ee1d source5306fbf2;19 Node tests pass; owner reached real callback and observed owner_provider_unavailable. Protected browser sessions and all keys unchanged.
FAILED_AVOIDED: Node fetch mocks did not model workerd redirect:error incompatibility; Cloudflare runtime/docs confirm error mode throws before a request. Do not replay the consumed callback code or publish it. Do not retry unchanged OAuth flow.
SCOPE: use supported manual redirect handling with explicit 3xx rejection in identity and GitHub bridge requests, actual workerd regression, tests and guarded keep-vars deployment, then fresh real Claude OAuth acceptance.
SUCCESS_SIGNAL: runtime accepts outgoing requests without unsupported-mode error, redirects cannot forward credentials, real owner callback and Claude GitHub tool acceptance.
FAILURE_SIGNAL: credential forwarding, unsupported runtime API, lost PKCE/identity/replay guards, source/deployment change or competing lease.
TEST_VALIDITY: test actual local workerd rather than only Node mocks; production changes must be substantive reviewed fixes, not audit probes. No CORTES/Android/clipper changes or Windows focus manipulation.
