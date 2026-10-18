# Anthares + Claude Free — stage 1 integration

STATUS: STAGED / NOT DEPLOYED. Changes are on `integration/claude-free-mcp-20261018`. Do not direct the owner to authorize the connector before deployment and real OAuth verification.

## Verified capabilities
1. Anthropic permits one remote custom MCP connector on the Free plan. Claude Code itself is not included in Free.
2. The Anthares Remote MCP server already exists at `https://anthares-ara-mcp.anthares1.workers.dev/mcp`; the current production server authenticates ChatGPT clients with PKCE and owner-approved OAuth.
3. The existing gateway previously accepted only ChatGPT OAuth client/redirect identifiers and keeps ChatGPT's authorized client pinned.
4. This branch adds exact Claude client IDs and the official `https://claude.ai/api/mcp/auth_callback` redirect. The Claude client bypasses only the *ChatGPT client-ID pin*, with a separate owner email-OTP approval. PKCE, access tokens, refresh tokens, expiry, replay protection and signature checks remain in place.
5. Claude scopes are restricted to `ara.read`. Remote execution, process control and file writes are still unavailable to Claude at this stage.

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

## GitHub write integration — remaining work
- Implement a **server-side**, narrowly scoped GitHub App installation token or fine-grained repository token; store credentials as hosting secrets, never in `CLAUDE.md`, GitHub issues, OAuth URL or chat prompts.
- Implement MCP tools with explicit repository allowlist, authenticated owner scope, exact SHA/HEAD checks, Test Hub lease check, branch names restricted to `claude/*`, and creation of draft PRs. Reject direct default-branch writes.
- Add positive/negative tests for path traversal, cross-repository access, concurrent editing, wrong blob SHA, unauthorized scopes, expiry and duplicate requests.
- Integrate with the existing Anthares Remote/Browser only through the signed, authorized control path; provide browser access separately and conservatively.
- When all mechanisms are deployed, validate a harmless edit to a disposable test file in a draft branch, then independently verify the PR on GitHub.

## No-cost boundary
Do not subscribe to Claude Pro, enable paid Claude Code, provision a paid Anthropic API key, activate billing, or consume exhausted GitHub Actions minutes. Free usage can be rate-limited. Do not promise autonomous unlimited execution.

Sources: https://support.claude.com/pt/articles/11175166-comece-com-conectores-personalizados-usando-mcp-remoto and https://support.claude.com/pt/articles/10167454-use-a-integracao-do-github
