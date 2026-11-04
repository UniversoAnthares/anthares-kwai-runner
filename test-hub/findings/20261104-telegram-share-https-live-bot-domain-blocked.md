# WordPress Telegram — compartilhamento HTTPS implantado; vinculação aguardando BotFather
STATUS: PARTIAL
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: Hostinger SSH WP-CLI and HTTPS static hash; official Telegram OAuth embed probe
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/222 ; https://github.com/UniversoAnthares/anthares-wordpress/pull/223
COMMIT: 35fde9380adb4179330bdf431d4c19448b8a7f7d
SUPERSEDES: test-hub/findings/20261104-telegram-bot-login-lease.md

## PROVEN — share manual
PR #222 merged, WordPress live Hostinger plugin PHP git blob 380fe5b6a825ac461bdb969e671d0b9ebd9da38a, JS blob 8d81ebb5b43c694f69092d3a43d24fb67a5a4487. JS served HTTPS 200 and hash exact; WordPress WPCLI forum topic 10898 rendered SHARE_BUTTON=PASS, TOPIC_LINK=PASS, PANEL_HIDDEN=PASS. JS simulated click triggers https://t.me/share/url?url=<topic>&text=<typed_message>; no tg:// dependency. PHP 8.5 lint PASS; manifest 605/605 PASS. Private backup verified and deployed staging cleaned. No Telegram messages sent.

## PARTIAL — authentic linkage
Existing wptelegram option has bot username @anthares2_bot and configured credential; Telegram getMe returned valid bot identity. Code-only PR #223 (draft) implements official Telegram Login Widget, HMAC verification server-side and WordPress ID mapping. PHP lint and QA manifest PASS. OAuth embed probe for origin https://anthares.us returns exact "Bot domain invalid". BotFather /setdomain anthares.us is required from bot owner before integrating this PR and testing signed account login. Previous Railway MTProto relay remains offline; no new Railway deployment or charges.

## Next
(1) Owner authorizes domain @BotFather /setdomain anthares.us for @anthares2_bot; (2) recheck OAuth embed, merge PR #223, backup+deploy+end-to-end identity; (3) original personal-account one-click MTProto send still needs no-cost relay solution, separately.
Lease closed PARTIAL.