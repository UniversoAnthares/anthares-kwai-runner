# Anthares + Claude Free — stage 1 integration

STATUS: STAGED / NOT DEPLOYED. Changes are on `integration/claude-free-mcp-20261018`. Do not direct the owner to authorize the connector before deployment and real OAuth verification.

## Verified capabilities
1. Anthropic permits one remote custom MCP connector on the Free plan. Claude Code itself is not included in Free.
2. The Anthares Remote MCP server already exists at `https://anthares-ara-mcp.anthares1.workers.dev/mcp`; the current production server authenticates ChatGPT clients with PKCE and owner-approved OAuth.
3. The existing gateway previously accepted only ChatGPT OAuth client/redirect identifiers and keeps ChatGPT's authorized client pinned.
4. This branch adds exact Claude client IDs and the official `https://claude.ai/api/mcp/auth_callback` redirect. The Claude client bypasses only the *ChatGPT client-ID pin*, with a separate owner email-OTP approval. PKCE, access tokens, refresh tokens, expiry, replay protection and signature checks remain in place.
5. The staged OAuth gives Claude `ara.read`, `github.read`, and `github.write` when explicitly requested and approved. `ara.write` is excluded. Arbitrary Windows remote execution and file writes remain unavailable to Claude.

## Before deployment
- Test the authorized published-client metadata URL actually sent by Claude in its current version; prefer the exact URI that successfully resolves to a matching client metadata document and includes the official callback.
- Verify OAuth discovery, invalid callback rejection, owner OTP, PKCE S256, replay rejection and token refresh in a non-production environment.
- Confirm client pinning of the connected ChatGPT MCP client is unchanged.
- Inspect existing deployments and Test Hub leases for concurrent Anthares control modifications.
- Deploy only after checks pass and no conflicting lease exists. Do not activate GitHub Actions merely to test authentication.

## After deployment: the one-time owner action
In Claude (web is preferred while mobile custom connectors remain beta), open **Personalizar > Conectores > Adicionar > Personalizado > Web**.
Enter:
- Name: `Anthares`
- Remote MCP URL: `https://anthares-ara-mcp.anthares1.workers.dev/mcp`
- Authentication: OAuth sign in; use Claude's published client identity.
Complete the *real Anthares owner approval*, never send the approval code to a model, issue, or repository.

Try a read-only instruction: `Consulte session_status e relate se o Anthares Remote está conectado, sem executar comandos.`
The tool call succeeding end-to-end is the required acceptance proof.

## GitHub write bridge — staged; credential and deployment pending
- Staged bridge code uses a **server-side** token in Cloudflare secret `ANTHARES_GITHUB_TOKEN`. It still must be configured; never paste it in chat, `CLAUDE.md`, issues, OAuth URL or repository. Restrict the fine-grained token to the five approved repos and permissions Contents read/write, Pull requests read/write and Metadata read.
- Implemented MCP tools `github_get_file`, `github_begin_task`, `github_create_branch`, `github_put_file`, and `github_draft_pr`; code enforces repository/branch allowlists, fresh SHA/HEAD, Test Hub lease and draft PR. Only the lease writer appends to the Test Hub on `main`.
- Implemented offline tests in `src/github-bridge.test.mjs` and `src/claude-client-policy.test.mjs`. At commit `92fd645fa7342929161836f558e2e666538f2b89`, 5/5 syntax checks and 11/11 Node tests passed; additional live OAuth replay, scope and duplicate-PR checks remain pending.
- Anthares Remote remains available to Claude for scoped read actions only, through its existing signed bridge. Anthares Browser has not been exposed to Claude.
- After configuring the server credential and deploying safely, use Claude to edit a disposable `claude/*` file, open a draft PR and independently verify the GitHub result.

## No-cost boundary
Do not subscribe to Claude Pro, enable paid Claude Code, provision a paid Anthropic API key, activate billing, or consume exhausted GitHub Actions minutes. Free usage can be rate-limited. Do not promise autonomous unlimited execution.

Sources: https://support.claude.com/pt/articles/11175166-comece-com-conectores-personalizados-usando-mcp-remoto and https://support.claude.com/pt/articles/10167454-use-a-integracao-do-github
