# Claude OAuth interoperability and scoped GitHub bridge: deployed, owner-visible approval pending
STATUS: PARTIAL
AREA: ara-mcp-claude-deploy, claude-session, claude-github-tools
DATE: 2026-10-19
COMMIT: 5306fbf2c6e7f478e9ffe1e8334a9da1fe4920bb
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/162
SUPERSEDES: 20261019-1052-lease-claude-acceptance-resume.md
LEASE: CLOSED pending personal visible GitHub owner consent. Acquire fresh lease before additional mutation.

## Baseline and actual browser findings
The source branch is integration/claude-free-mcp-20261018; main remains separate and PR162 remains draft. The interrupted prior attempt had not deployed b7bd1848, verified by the Cloudflare deployment history on resume. No other MCP source/deployment lease was active; newer main changes affected only the independent Kwai publisher and were preserved. GitLab main still has the earlier gateway index blob273d1af68ee486ee0291d6c1fa0f025a270020f9 and no Claude GitHub module; no blind peer overwrite was performed.

The actual Claude Free account login was personally completed by the owner. Its existing Anthares custom connector was used, without adding or modifying other connectors. Browser acceptance identified and corrected:
- Referrer-Policy:no-referrer caused the legitimate form Origin to be null and hit invalid_origin. HTML now uses same-origin policy; strict server Origin verification remains intact.
- Anonymous MCP WWW-Authenticate advertised only the old ara scopes, so Claude requested no GitHub access. The challenge now advertises github.read/github.write alongside supported ara scopes, and Claude's actual consent page showed ara.read,github.read,github.write. ara.write is still narrowed out for Claude.
- Chrome blocked the form's official GitHub redirect under form-action self. A real securitypolicyviolation event identified form-action. CSP now permits self and the exact https://github.com origin only.

Corrected versions were tested before each intentional keep-vars deployment. Latest Worker13f5ee1d-33fd-4310-b2ca-f16e1b2871ca deployed from5306fbf2 (Remote job0c3e14787eb4e23d235dfb4dc3bd40af). Immediately previous version00c47732-e137-4f13-8014-4de6dc45b4c0 remains the rollback baseline with the same protected credentials.

## GitHub bridge corrections
Preparing the real write acceptance revealed that begin_task appended a Test Hub commit but did not return the resulting source HEAD; a client could not safely create its branch with the pre-lease SHA. The result now includes base_sha after lease validation. File reads return head_sha and fetch content by immutable commit.

The old check-then-Contents-write sequence was not atomic against another file changing after the final HEAD read. File edits now use GitHub createCommitOnBranch with expectedHeadOid, with no unsafe fallback after rejection, followed by immutable committed-content verification. This is restricted to the same claude/* branch/path/lease/owner policy. An explicit GitHub User-Agent was added. Generated Test Hub leases now include required baseline, failure, success and validity signals. No unrestricted shell or new paid executor was exposed.

## Proven verification
19/19 Node tests pass plus signed capabilities regression (Remote job5ad8cd3c70a24058c04aa61fe23612a7). New tests prove immutable file reads, post-lease fresh HEAD and a simulated atomic stale-HEAD rejection with no secondary write. An initial patch harness stopped before writing because the source used CRLF; normalizing line endings corrected the harness. This was not a production logic failure.

Latest live preflight jobdbdd22dbfbbc002e536000d3e42010ca: OAuth page200; provider start302 to GitHub; S256; empty GitHub identity scopes; secure HttpOnly cookie; no email dependency. Health/discovery200, anonymous MCP401 and forged callback403. Existing ChatGPT session_status and signed capabilities remain connected and operational after all deployments. A transient existing leased job was observed and left untouched; no unrelated queue was canceled.

## Real remaining gate
The real flow reached GitHub's Authorize Anthares Owner Authorization page for UniversoAnthares and displayed Public data only. GitHub's own current client script requires real focus, visible document, viewport intersection and a focus delay before enabling the button. Browser inspection showed visibilityState=hidden despite a normal headful dedicated Chrome session; no attribute removal, emulated visibility or alternate approval endpoint was attempted. A normal dedicated-window activation attempt through Anthares Remote was explicitly rejected by its policy: interactive desktop or focus manipulation forbidden by ARA headless policy (job61e7b5612e9b1ee4360d40def1bdbd1b). The owner was asked to place that dedicated window in focus and click Authorize UniversoAnthares.

Owner GitHub provider callback/token issuance, actual Claude tools/list and GitHub file read/edit/draft PR are still NOT PROVEN. No claude/* acceptance commit or draft acceptance PR is claimed. If the ten-minute request expires while waiting, restart only the connector authorization from the existing Claude session after the owner returns. Do not mark the complete integration operational before those real tool calls are independently verified.

The original sender-domain problem remains documented in20261019-0059-claude-owner-github-oauth-deployed-partial.md; contato@anthares.us delivery was not established. All existing secrets, PKCE, client pinning and identity allowlists remain protected. No CORTES/Android/clipper mutation, Windows restart/shutdown/logoff, paid service or card enrollment occurred.
