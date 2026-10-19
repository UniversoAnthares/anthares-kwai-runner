# Claude Free Anthares MCP: real acceptance
STATUS: PROVEN
AREA: claude-github-tools / ara-mcp-claude-deploy / claude-session
DATE: 2026-10-19
RUN: https://claude.ai/chat/1f73a1f0-743c-4fc0-871c-f764fd991afe
COMMIT: dd14ef5d0bb277cfa8791f54c6f92e3b81234d9d
SUPERSEDES: 20261019-1105-claude-oauth-interoperability-and-branch-fencing-partial.md; 20261019-1202-claude-worker-provider-runtime-validation.md; 20261019-1150-lease-claude-worker-provider-runtime-fix.md; lease-claude-github-20261019121300-015497d5.md
LEASE_STATE: CLOSED

## Proven acceptance
The owner's legitimate Claude Free session shows Anthares connected at the production MCP URL and a 20-tool catalogue. Actual Claude conversation above invoked Anthares session_status and github_get_file, returning connected=true, backend vercel-neon, current heartbeat, AGENTS.md blob b99e0de7761d25667679953a7b69cd3e46a483a4 and Test Hub README blob 020b140bcf8dd4c901f71ea424a851e6ff1775e6 at main HEAD 137c1d08a085f13a6e89eec6efd6bf3b6fe9361c. Authenticated tool calls prove the owner-authorized OAuth token works end to end; no secret or callback code is recorded here.

Claude then read the recent findings, acquired its own 20-minute lease, and created claude/mcp-acceptance-20261019-1210 from returned post-lease base 8907a056d2a02e9803bc99a4bbe643fb09c8b3f5. It checked the disposable path was absent (404), created docs/claude-mcp-acceptance-20261019-1210.txt with optimistic concurrency, read it back, and opened draft PR #164 without merging.

Independent GitHub connector verification: PR https://github.com/UniversoAnthares/anthares-kwai-runner/pull/164 is open, draft=true, one changed file, one commit 2c320a373c648b13f9766d192cc15c0d181ceeb8; file blob 8afd94029eb32b7661540a03a3a17f9908375785 contains exactly the harmless acceptance line and newline. No default-branch code was written by Claude.

## Corrections and tests
Production source dd14ef5d; Worker version 24ffad76-20a0-4911-b6c9-465ad1b135b2; previous 4773fa0f-2ea6-468e-abe1-c8e62cbe43b0. Existing secrets preserved. The bridge's reserved-path write check initially blocked mandatory preflight reads too: only direct Markdown finding reads are now permitted; findings writes and vault reads remain denied. 23 Node/workerd tests and signed capabilities regression passed (Remote job 4ef39c5ae1d54a6455f42fb20c0ed4d0). Deployment job b0654a463706974dadfa36a40560aa23. Workerd manual redirect protection, exact owner identity, PKCE, single-use codes, scopes, expected-head atomic writes and ChatGPT contract remain tested.

## Boundaries / remaining items
Email sender-domain delivery remains unavailable; GitHub owner identity OAuth is the operational alternative. Claude Remote scopes intentionally remain read-only; arbitrary command/test execution is not exposed to Claude. Integration source is in draft PR #162 and is deployed, but not merged to main. The disposable PR #164 must remain unmerged. This finding closes both listed task leases; future mutations require fresh leases. Other platform publication acceptance is outside this finding. No CORTES, Android, SSH or anthares-clipper behavior was changed.
