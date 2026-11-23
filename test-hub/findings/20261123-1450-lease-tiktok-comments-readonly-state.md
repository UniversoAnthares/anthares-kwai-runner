# Lease — TikTok deferred comment read-only state isolation
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-11-23
RUN: none (CAPTCHA still pending)
COMMIT: 637301342fb17fdbd9337664b9591d62c19c25f1
SUPERSEDES: test-hub/findings/20261123-1425-tiktok-comments-hold-quota-pr-staged.md
LEASE_OWNER: chatgpt-gpt6-tiktok-readonly-hardening-20261123
LEASE_EXPIRES_AT_UTC: 2026-11-23T15:17:00Z
SCOPE: tools/cortes_tiktok_deferred_comments.py; tests/test_cortes_tiktok_deferred_comments.py; optional per-account read-only secret gate in the existing comments workflow. Existing PR #2756 and main source sha checked.

## BASELINE_PROVEN
On 2026-11-23 Neon snowy-tree-98635265/br-dark-rice-b7jf2e9e: universo.anthares 1 pending/1 uncertain/0 posted; lucasrosalem4 5 pending/1 uncertain/0 posted. Both sessions have previously yielded CAPTCHA. PR #2756 has the gated Chromium download and passing previous contract run 45193541765.

## FAILED_AVOIDED
The current main() loads state_from_secret() or load_canonical_state() before checking that TIKTOK_COMMENT_BROWSER_CLEARED=false; despite being read-only on schedule/push, it still decrypts a session and may fail before reading pending Neon. No CAPTCHA bypass, no new video, no retry of uncertain source and no claim that cloud session was verified.

## SUCCESS_SIGNAL
With clearance=false, tests prove that both accounts can execute main() and reach read-only pending via OIDC without loading either TikTok browser state or Chromium. With clearance=true, tests prove canonical session load remains required before any action. Existing idempotency and identity tests pass. No real browser/comment action permitted during CAPTCHA.

## FAILURE_SIGNAL
Read-only HOLD fails due to a missing TikTok session; browser is used in scheduled/push mode; or a test accidentally reserves or publishes a comment.

## TEST_VALIDITY
Mocks only; one CI contract run after patch. No live CAPTCHA retry. Diff limited to comment-only files. GitLab peers lack same workflow, no mirror writes. Owner lease append-only.
