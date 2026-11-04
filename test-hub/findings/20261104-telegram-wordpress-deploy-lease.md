# Telegram WordPress — deploy manual do grupo
STATUS: RUNNING
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: pending
JOB: ChatGPT user requested "implante"; PR https://github.com/UniversoAnthares/anthares-wordpress/pull/221
COMMIT: WP main 6a76d0f62d9dcb5544609906a3e222ea20929690; branch e643e7a74a88f3ba7d8ba759fde4361b399ae56b
SUPERSEDES: test-hub/findings/20261104-telegram-manual-deeplink-ui-partial-closure.md

## Baseline e owner
Hostinger live git blobs: PHP 3f26c4b2224d950c383ce786b50944df0eea6145, JS 68c88bc30edf28b442f6a0c61ed8092325fcb465, CSS 761b27e2f8cdb501b3de06834d293990048de361. Site WordPress can be reached through authorized SSH alias anthares-hostinger. Vercel GitHub PR CI status FAILED due to account block, not accepted as QA.

## FAILED_AVOIDED
Avoid reopening bare t.me landing, changing arbitrary WP plugins, deploying Railway before proof of zero cost, or transmitting Telegram messages as part of test. GitLab main diverged/older. A different agent may modify files; require SHA comparison immediately before atomic deploy. No local computer staging.

## SUCCESS_SIGNAL
Whole-file PHP lint + JS syntax and manifest QA PASS; GitHub PR merge gated by fresh HEAD; atomic Hostinger deploy limited to PHP and JS with protected backup; WP render check, topic 10898 URL, HTTP200 JS/PHP version and exact deployed git blobs.

## FAILURE_SIGNAL
Site unavailable, PHP lint failed, unexpected source hashes, concurrent lease/change, failed preflight, or deployment without rollback.

## TEST_VALIDITY
Static and HTTP probes prove installed files, not actual Telegram app rascunho or publication. Relay remains separate blocked item.
## Lease
Owner ChatGPT. Start 2026-11-04T12:03:02.774Z. Expires 2026-11-04T12:31:02.774Z. 28 minutes; close append-only.
