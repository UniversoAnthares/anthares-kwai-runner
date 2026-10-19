# Claude MCP owner authorization: email cause identified, GitHub fallback deployed
STATUS: PARTIAL
AREA: ara-mcp-claude-deploy
DATE: 2026-10-19 UTC / 2026-10-18 America/Cuiaba
SUPERSEDES: 20261019-0042-lease-claude-oauth-email-recovery.md
LEASE: CLOSED awaiting owner-only Claude login; no competing deployment should be started without a fresh lease.
COMMIT: e97cb3836c01479ec21603a6586193b7bb21abad
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/162

## Exact cause
Production AUTH_EMAIL_SEND binding existed and AUTH_EMAIL_FROM was noreply@anthares.us. Read-only configuration inspection found no DNS zones or verified routing destinations on Cloudflare account anthares1. A valid Claude authorization request returned503; captured Worker log: oauth_email_delivery_error email from anthares.us not allowed because domain was not found (Remote job330d0bff61436fe77b20a6c580031b9a). Sender change alone cannot onboard the domain. Owner-requested contato@anthares.us REST attempts returned400 email.sending.error.email.invalid; delivery was not established. The configured sender now uses contato@anthares.us, while the operational authorization path no longer requires email.

## Correction and protected provisioning
Official GitHub OAuth owner application3944280 was registered by the existing isolated Anthares Browser session. The owner personally completed GitHub Confirm access. Its credential was transferred directly from the authenticated page into Cloudflare secret ARA_OWNER_GITHUB_CLIENT_SECRET, without disclosure or plaintext credential files. Public client ID Ov23li1xRCECmyI7JYsn; pinned numeric owner81930373 (UniversoAnthares); no repository OAuth scopes requested. Existing ANTHARES_GITHUB_TOKEN and signing/OAuth secrets were preserved.

The identity provider leg uses S256 PKCE and an AES-GCM encrypted HttpOnly/Secure/SameSite=Lax browser cookie, exact callback, browser-state binding, ten-minute expiry and durable one-use callback consumption. Owner ID is verified before the original pending authorization is consumed and the MCP authorization code issued. Original Claude PKCE, scope narrowing, refresh rotation and replay checks remain enforced. Owner identity tokens are not persisted and are revoked after use where provider connectivity permits. GitHub-only mode rejects the email-approval POST; inactive email fallback now has a five-attempt bound. Current ChatGPT client pin/token behavior is preserved.

## Proven tests and deployment
Remote job3a66b99fbc8ce404e3f5d8d7b5c25edf:16/16 Node tests pass, signed capabilities regression passes, Wrangler dry-run succeeds. Tests cover successful mocked owner flow, wrong owner, origin/state/cookie forgery, cookie expiry, PKCE mismatch, authorization-code reuse, refresh reuse, scope restrictions, existing ChatGPT access, branch/path/lease/SHA restrictions and draft PR policy. A first test assertion incorrectly expected scope rejection rather than the existing safe narrowing behavior; the test was corrected to assert the actual narrowed grant, without weakening production policy.

Deployment Remote job7535ab5134f4b7af9993f2e0aa880cfd: Worker version89b087e4-0e65-4c67-82ca-3445bb769f41, sourcee97cb383. Previous exact version69e8c572-7a8a-410e-a164-31dbdd3829b6 contains the new protected secret and can be used for rollback. Keep-vars deployment retained all existing secrets. Production health/discovery200; signed Remote connected with queued/leased/uncertain all0; capabilities returned supported signed contract. Anonymous MCP401 and forged owner callback403 (jobfd376156bc68d2073a90c0144f40438a).

Live OAuth-start acceptance jobffc231f0223100cb7a4a99282d8037ec: authorization page200, owner-provider redirect302 tohttps://github.com, S256, empty provider repository scopes, secure encrypted cookie, no email dependency. This is not a completed Claude authorization and must not be described as such.

## Remaining owner-only gate
The visible isolated administrative browser is on the real Claude login page. The owner was asked to sign into their Claude account directly. No model received a password or login code. Once authenticated, reconnect Anthares and perform actual Claude-issued tools/list, github_get_file, disposable claude/* branch edit and draft PR; independently verify outputs. Neither those Claude tool calls nor the provider callback in production are yet proven. PR162 remains draft, not merged. Generic remote shell remains unavailable to Claude through this scope policy; do not claim a newly exposed unrestricted test executor or Browser tool.

All computer operations used the existing Anthares Remote; source publication used the already authorized GitHub session. No paid service, CORTES code/publication change, Android mutation, reboot, shutdown or logoff was introduced. Diagnostic tails were stopped before real owner authorization to avoid collecting callback credentials. Do not repeat the failed email path without changing domain/destination readiness. A fresh lease is required to resume remaining acceptance.
