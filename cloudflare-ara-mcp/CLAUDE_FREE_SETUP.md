# Claude Free and Anthares MCP

Endpoint: https://anthares-ara-mcp.anthares1.workers.dev/mcp

## Owner authorization

Production uses the official GitHub authorization flow to identify the owner by the pinned numeric GitHub user ID 81930373 (UniversoAnthares). The identity application requests no repository scopes. Its client secret lives only in Cloudflare secret ARA_OWNER_GITHUB_CLIENT_SECRET; the separate repository bridge credential remains ANTHARES_GITHUB_TOKEN.

The owner starts a normal Claude connector authorization, reviews the requested Anthares scopes and selects Autorizar com GitHub. Browser state and the provider PKCE verifier are encrypted in an HttpOnly, Secure, SameSite=Lax cookie. Exact callback, browser state, identity, expiry and one-time callback/pending/code consumption are checked before issuing the original MCP authorization code. Claude's outer PKCE and refresh-token rotation remain enforced. Existing ChatGPT tokens and client pinning are preserved.

Email diagnostics on 2026-10-19 UTC identified AUTH_EMAIL_SEND as present but rejected noreply@anthares.us with: email from anthares.us not allowed because domain was not found. The account had no DNS zones or verified routing destinations. A user-requested contato@anthares.us REST test also failed (email.invalid); successful delivery was not established. The configured email sender now uses contato@anthares.us, but owner authorization no longer depends on email. Do not mark email delivery as fixed without domain onboarding and a delivery receipt.

## Connect and validate

In Claude settings/connectors, add or reconnect Anthares using the endpoint above and OAuth. Free accounts support one custom remote connector and remain subject to their usage limits. Complete any personal Claude/GitHub authentication directly in the dedicated browser; never paste codes or tokens into chat.

Acceptance requires actual Claude tool calls: session_status, github_get_file, then a disposable claude/* branch change and draft PR. Direct HTTP or mocked tests alone do not prove Claude integration.

## Scoped GitHub changes

The bridge exposes github_get_file, github_begin_task, github_create_branch, github_put_file and github_draft_pr. Repository allowlists, claude/* branches, Test Hub leases, current HEAD/blob checks, reserved/secret-path rejection and draft-only PRs remain mandatory. Claude receives ara.read/github.read/github.write as granted; ara.write is excluded. It cannot invoke unrestricted Windows shell, direct main edits or publication controls through this integration.

## Verification and operation

Run node --test src/claude-client-policy.test.mjs src/github-bridge.test.mjs src/owner-github-auth.test.mjs and node capabilities.test.mjs from cloudflare-ara-mcp. The integrated tests cover owner identity, cookie tampering, callback state, expiry, PKCE, code/refresh reuse, scopes and existing ChatGPT token behavior. Deploy with wrangler deploy --keep-vars after checking current deployment and Test Hub lease. Keep all signing and OAuth secrets unchanged.

For rollback use the immediately recorded previous Worker version, not a stale historical reference. Preserve ARA_OWNER_GITHUB_CLIENT_SECRET so a redeploy does not require generating another credential. If changing the owner account, require an explicitly authorized identity reconfiguration; do not relax the numeric ID allowlist.
