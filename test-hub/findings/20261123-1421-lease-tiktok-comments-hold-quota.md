# Lease — TikTok comment-only HOLD runtime quota optimization
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-11-23
RUN: none (no comment run allowed during CAPTCHA)
JOB: none
COMMIT: abf710c50fe483e683adcb045a32af3c180aab9d
SUPERSEDES: test-hub/findings/20261122-0955-tiktok-comment-neon-release.md
LEASE_OWNER: chatgpt-gpt6-tiktok-comment-ci-20261123
LEASE_EXPIRES_AT_UTC: 2026-11-23T14:45:00Z
SCOPE: .github/workflows/cortes-tiktok-deferred-comments.yml only, feature branch, PR review.

## BASELINE_PROVEN
PR #2751 merged at 1572b8adae1c9786d56ee759a4dd23f1ffce2878; both CAPTCHA pending; the alternate Neon comment ledger observed 2026-11-23 contains posted=0, uncertain=2, pending=6. Scheduled and push events use browser-clearance=false. GitHub Actions currently installs Chromium on every HOLD run even when no browser attempt is permitted.

## FAILED_AVOIDED
Do not repeat CAPTCHA-blocked browser clicks or start a new video. Preserve one-shot comment reservations, the two uncertain receipts, both account identities and pending queue. Browserless has 7/1000 units remaining and no authenticated TikTok profile, so do not consume it.

## SUCCESS_SIGNAL
On branch: workflow YAML remains valid; both jobs install requests/required crypto but download Playwright/Chromium only after an explicit per-account captcha-cleared workflow_dispatch. Existing comment-only unit/CI checks green. Zero media or comment effects.

## FAILURE_SIGNAL
Any scheduled/push job can still download Chromium; dependencies missing for read-only HOLD; accidental authorization of browser, video upload or mutated receipts.

## TEST_VALIDITY
Use static workflow checks and existing unit tests. No live TikTok comment tests until legitimate human challenge resolution in the same authenticated session. A green CI is not evidence of a posted comment.

## Read-before-write
GitHub main HEAD abf710c50fe483e683adcb045a32af3c180aab9d, workflow blob 7471699570b141c5bd0f875ddf7322d021aabb5d. Both known GitLab peer projects returned 404 for the workflow; no mirroring or peer write.
