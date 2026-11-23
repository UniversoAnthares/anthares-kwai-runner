# TikTok comment-only HOLD: quota optimization staged and lease closed
STATUS: PARTIAL
AREA: tiktok-publish
DATE: 2026-11-23
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/45193541765
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/45193541765/job/137757857281
COMMIT: 80e21d47672d5daf63f96498a975f96db89ab9e1
SUPERSEDES: test-hub/findings/20261123-1421-lease-tiktok-comments-hold-quota.md
LEASE_OWNER: chatgpt-gpt6-tiktok-comment-ci-20261123
LEASE_STATUS: CLOSED
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2756
DEPLOYMENT: NOT_APPLIED; draft PR, no main merge

## Resultado comprovado
Both primary and secondary comment-only workflow jobs install the existing import dependencies and download Playwright/Chromium only under TIKTOK_COMMENT_BROWSER_CLEARED=true. Static inspection verified two gates. Existing contract CI run 45193541765 passed, including the five-window deferred comment security/idempotency tests. Source GitHub main SHA abf710c50fe483e683adcb045a32af3c180aab9d at snapshot; target workflow blob 7471699570b141c5bd0f875ddf7322d021aabb5d. GitLab peers returned 404 for this file, no fallback/mirroring performed.

## Live read-only evidence
On 2026-11-23 Neon project snowy-tree-98635265 branch br-dark-rice-b7jf2e9e returned by account: universo.anthares sources=2 pending=1 posted=0 uncertain=1, lucasrosalem4 sources=6 pending=5 posted=0 uncertain=1. No SQL write, no new video, no comment attempt, no refresh to the original quota-exhausted Neon. CAPTCHA for both accounts remains an external security gate. Browserless balance=7/1000 free units, without TikTok authentication; no Browserless paid usage attempted.

## Acceptance boundary
CI success proves the code contract, not that a real comment exists. After legitimate human verification in the relevant TikTok session, only an approved one-shot workflow_dispatch for that account may attempt a pending source, followed by independent verification of the visible comment and Neon posted receipt. Two uncertain sources remain excluded. PR remains draft for review; no production schedule, secret, primary, video or queue mutation was made.

## Rollback
Discard PR branch or revert the single workflow change before promotion. No runtime effect to roll back now.
