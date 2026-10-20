# Anthares multiagent — ChatGPT GitHub Issues -> Claude Code real
STATUS: PROVEN (ChatGPT and Claude Code); WORK_SESSION: NOT_TESTED
AREA: anthares-multiagent-live-acceptance
DATE: 2026-10-20
SUPERSEDES: test-hub/findings/20261020-0152-multiagent-work-collab-partial.md (re: live gateway); test-hub/findings/20261020-0200-router-retry-partial.md (re: bootstrap timeout)
BASELINE: GitHub Claude Free owner run 39352658418 successful with get_claude_code_result ready=true.
LEASE_STATE: CLOSED AFTER EVIDENCE REVIEW
ENTRY_ISSUE: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/230
GATEWAY_RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39356597262
CLAUDE_RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39356635285
DEPLOY_WORKER: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39355914581
GATEWAY_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/226
RETRY_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/229
REQUEST_ID: f36984a3-1116-5440-acd9-da46e83a6b2d
ARTIFACT_ID: 12235437781
MERGED_COMMITS: gateway 5d032b7e71294881699211d3a700bf1a90ae6af3; retry 4cae5ec1cd46beaca4c635a9ae5012699f855cd3

## Evidence
1. ChatGPT official GitHub connector created owner-authored issue #230, format `[ANTHARES-COLLAB-PLAN]` plus exact JSON schema/source=chatgpt/mode implicitly plan.
2. Native GitHub `issues.opened` started gateway run 39356597262. Contract job passed 39 security/regression tests. Owner verified as `UniversoAnthares` (user ID 81930373). Runner wrote CLAIM and DISPATCH_ACCEPTED comments, unique deterministic UUID from GitHub issue ID.
3. Nested Claude Code run 39356635285 started as `github-actions[bot]` and passed `ANTHARES_COLLAB_OWNER_ORIGIN_VERIFIED=f36984a3-1116-5440-acd9-da46e83a6b2d`. Mode plan only; bot edit gate unchanged; no main mutations.
4. Native cloud runner completed `static-check` and `execute` jobs `conclusion=success`. Temporary Gemini/9Router/Claude Code provisioned remotely, no PC/VPS runtime. Artifact `anthares-free-claude-result-39356635285` id 12235437781 downloaded and inspected: ZIP STORE member `anthares-claude-result.txt` starts with `ANTHARES_COLLAB_CHATGPT_WORK_OK`, followed by two actionable JavaScript verification steps.
5. Gateway run 39356597262 also `conclusion=success`, issue #230 final comment `[ANTHARES-COLLAB] COMPLETED id=f36984a3-1116-5440-acd9-da46e83a6b2d conclusion=success run=https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39356635285`; exactly one nested dispatch from that issue.
6. New read-only Claude Free MCP tools `collab_list_tasks` and `collab_get_task` merged on main and deployed in Cloudflare run 39355914581 (OAuth GitHub owner, control_ready, anonymous tools/list 401 validated); same client may need discovery refresh for extra tool names.

## Negative case and causal fix
The earlier distinct issue #227 was not repeated. Its relay run accepted; Claude nested run 39355978335 failed at 9Router readiness timeout after direct Gemini model probes passed. Relay correctly posted `COMPLETED conclusion=failure`, did not resubmit. PR #229 changed only the harmless 9Router probe with bounded transient retries, required real text and retained security. Subsequent issue #230's nested run succeeded. No false positive success signals used.

## Actual scope and remaining acceptance
- ChatGPT -> shared issue -> GitHub Actions -> remote Claude Code -> artifact + issue completion: PROVEN in production.
- Existing direct Claude Free -> Anthares -> Claude Code -> result: separately PROVEN by owner through real Claude session/run 39352658418.
- Shared read-only issue mailbox Cloudflare MCP deployed and tested via bundle + anonymous denial, but **NOT YET owner-Claude UI-called**. Refresh Claude MCP catalog and invoke `collab_get_task(repo,issue_number=230)` for client-layer acceptance if desired.
- Work can work on same GitHub Issues/PRs with the installed GitHub connector in Work mode. **Work session was not invoked during this run; end-to-end Work-specific origination/review NOT_TESTED.** Requires explicit Work-mode task in owner session to verify.
- No direct automated Claude.ai↔ChatGPT conversation, no auto-initiated Work task, no paid service or billing; GitHub/Gemini free quotas and public issues privacy constraints remain.
- Preserve required reviewed PRs; do not auto-merge/force-push; never put secrets or private prompts in public issues.
