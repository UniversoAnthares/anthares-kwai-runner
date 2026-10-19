# Claude OAuth: production runtime correction

UTC: 2026-10-19T12:02:00Z
Scope: PR #162; Cloudflare anthares-ara-mcp. Supplements active lease 20261019-1150-lease-claude-worker-provider-runtime-fix.md (expires 12:18 UTC).

## Proven failure and correction
The real owner callback returned owner_provider_unavailable. Cloudflare workerd rejects Request redirect mode `error` before issuing a network request. Both provider identity exchange and the scoped GitHub bridge used that mode. A shared secure-fetch helper now uses manual redirects and rejects every 3xx response without forwarding credentials. Safe diagnostics expose only the failed stage, never codes, tokens, provider URLs or exception bodies.

Real browser CSP observations also required allowing the trusted GitHub and validated Claude/ChatGPT callback hosts in form-action. Exact server-side redirect URI validation remains enforced.

Source: dc4ccf5047b90035ed847abeb16a180a6354545b on integration/claude-free-mcp-20261018.
Production version: 4773fa0f-2ea6-468e-abe1-c8e62cbe43b0.
Previous version: 711209f4-ad21-46bc-b603-0d16a78f565e.
Deploy preserved all existing secret bindings and signing keys.

## Validation
22 Node/workerd tests passed, including actual workerd reproduction of unsupported redirect mode, successful manual-mode production helper, and redirect rejection without a second request. Capabilities regression test passed. Anthares Remote remains operational for authenticated execution.

## Acceptance still pending
A fresh real Claude OAuth flow and actual Claude GitHub tool read/write/draft-PR have not yet been proved. Do not interpret deployment or unit tests as acceptance. The dedicated browser currently has competing navigation into unrelated GitLab/Vercel connectors; no unrelated approval was submitted by this task. Owner coordination has been requested before continuing navigation.

Email delivery remains unavailable for the unverified sending domain; the secure GitHub owner-identity alternative removes that dependency while preserving PKCE, exact numeric owner identity, scope restrictions, one-use codes and protected tokens. No CORTES, Android or anthares-clipper changes were made.
