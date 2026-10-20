# Anthares ChatGPT + Claude Code + Work — shared GitHub collaboration gateway
STATUS: PARTIAL
AREA: anthares-multiagent-work-bridge
DATE: 2026-10-20
SUPERSEDES: test-hub/findings/20261020-multiagent-work-lease.md
BASELINE: GitHub direct Claude owner OAuth E2E run 39352658418 success and Claude caller get_claude_code_result ready:true.
ISSUE: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/222
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/226
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39355622185
CI_BRIDGE: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39355622093
RUNNER_STATIC: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39355622176
LEASE_STATE: CLOSED AFTER PR VALIDATION (pending merge and production acceptance)

## Goal
Re-use existing free ephemeral cloud Claude Code/9Router/Gemini to share task dispatch, tracking, result links and reviews among ChatGPT, Claude Free and ChatGPT Work. GitHub is common state. Do not imply that Work can be launched autonomously by an undocumented API.

## Executed and proven
- Owner-authored GitHub issue #222 created via ChatGPT GitHub connector. GitHub user `UniversoAnthares` and numeric ID `81930373` confirmed independently. Design issue is NOT automatically dispatched.
- Proposed gateway `tools/anthares_collab_gateway.mjs`: only strict JSON issue of title `[ANTHARES-COLLAB-PLAN] `, pinned owner both issue and event sender; source `chatgpt|work|claude` is attribution-only, not access rights; plan-only max 1600 characters. Deterministic UUID per immutable issue ID. CLAIM comment before dispatch, duplicate suppression, explicit uncertainty state, bounded status polling and links. No auto merge.
- New issue-triggered Actions workflow `.github/workflows/anthares-collab-plan.yml` calls existing free Claude Code workflow using job-scoped `GITHUB_TOKEN`, permissions actions:write/issues:write/contents:read.
- Existing `.github/workflows/anthares-free-claude.yml` preserves owner actor path; bot-origin `workflow_dispatch` only permitted after strict owner issue number+task+mode+request_id verification, no edit by bot.
- New Cloudflare MCP tools `collab_list_tasks` and `collab_get_task` are read-only under existing `github.read` OAuth; no GitHub secret exposed, no new OAuth scope. Changed `github-bridge.mjs` imports; deploy workflow already watches that module for reviewed main merges.
- Work lane via authenticated GitHub Issues and PRs, documented in `docs/anthares-collab/README.md`. Work mode cannot be invoked or certified from this Chat session.
- CI multiagent run `39355622185`: `ANTHARES_COLLAB_GATEWAY_CONTRACT=PASS`, 39 tests, zero failures; dispatch job skipped on PR (expected).
- CI original Claude bridge run `39355622093`: `ANTHARES_CLAUDE_MCP_DISPATCH_CONTRACT=PASS`, 25+6 tests zero failures, `ANTHARES_CLAUDE_MCP_WORKER_BUNDLE=PASS` on Wrangler dry-run.
- Original Claude Code runner regression `39355622176` static-check completed success; execute skipped on PR (expected).

## Not yet proven / blocker
- Changes are in PR #226 only, not on default branch. GitHub issue trigger requires workflow in default branch; Cloudflare deployment is main-triggered. No production Work/ChatGPT issue -> Claude Code run should be claimed until merged and real owner-created canary passes.
- Ruleset `proteger-main` blocked merge of PR #218 with `Restrict updates`, even after tests; must inspect current ruleset and preserve non-fast-forward/delete/review rules. Do not bypass protections, force push or publish branch-only code into production.
- Work itself must be initiated by user in Work mode with GitHub connected. GitHub Issues/PRs can serve as shared queue, but this does not create a live Work session or enable unbounded autonomous Claude.ai-to-ChatGPT conversation.
- No paid resources/PC runtime introduced; potential public issue privacy limits, Gemini quota, GitHub Actions quota remain.

## Acceptance still needed
After authorized merge: create exactly one benign issue `[ANTHARES-COLLAB-PLAN] ...` from ChatGPT GitHub connector; verify claim, dispatch ID, remote run finished, artifact and issue completed comment. Connect Claude Free and call `collab_get_task` after reload; start Work mode and verify it can read and review issue. Append new PROVEN finding only after this observable evidence.
