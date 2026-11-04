# Telegram — vínculo por /start e grupo Web sem prévia
STATUS: RUNNING
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: code and production preflight
JOB: ChatGPT — user requested conclude Telegram issues
COMMIT: wordpress main 35fde9380adb4179330bdf431d4c19448b8a7f7d
SUPERSEDES: test-hub/findings/20261104-telegram-share-https-live-bot-domain-blocked.md

## BASELINE_PROVEN
WordPress JS HTTP200 and PHP from latest deployment. Current share uses t.me/share/url, confirmed to show preview; account link AJAX hits MTProto Railway offline. Bot @anthares2_bot configured in wptelegram option; getMe valid, no webhook configured. Telegram discussões plugin has a DIFFERENT token; do not interfere. BotFather domain auth is blocked, so this repair uses official Bot API /start handshake without relying on OAuth domain setup.

## FAILED_AVOIDED
No t.me/share/url intermediary, no tg:// OS handler, no duplicate bot token or paid service. Use existing Hostinger, signed one-time /start challenge and WP REST webhook with secret header. Personal-account MTProto sending remains independent, do not claim that bot login authorizes sending as user.

## SUCCESS_SIGNAL
PHP8.5 lint; JS parser; QA 605/605; exact blob deploy backup; start + signed webhook + AJAX status integration with real bot account. No real group publishing.
FAILURE_SIGNAL
Webhook update invalid, existing webhook conflict, unauthenticated link, cross-user link, group chat mixed up, stale code, nonzero cost.
TEST_VALIDITY
Simulated POST and webhook contract are partial; only Telegram real /start and browser validation prove full linkage.
LEASE
owner ChatGPT; start 2026-11-04T13:49:58.817Z; expiry 2026-11-04T14:14:58.817Z; 25 minutes.