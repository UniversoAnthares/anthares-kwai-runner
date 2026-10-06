# Targeted help — custom Kwai executor + Cloudflare deploy
STATUS: OPEN
DATE: 2026-10-06

Closed and do not repeat: Kwai Direct Auth Entry QA30 run 37462410069 exhausted 30/30 after harness fixes; direct non-exported Activities and guessed kwai://login* routes are discarded. TikTok/Kwai safety, dedupe, Android baseline, HLS, APK discovery, TikTok reconciliation remain closed/proven.

Active: TikTok 30 Environment Replacement Matrix run 37463242183 is queued; do not start a competing real publication.

Cloudflare: public deploy run 37463135822 failed before wrangler because CLOUDFLARE_API_TOKEN is empty. This is a deployment credential boundary, not a control-plane logic failure.

Specific help requested:
1. Kwai: implement the Anthares-owned persistent cloud Android executor: normal in-app auth only, encrypted snapshot/restore, READY proof, account/session-generation validation, existing queue lease_generation/fencing, serialized publish/LIVE, fail-closed AUTH_REQUIRED.
2. Kwai LIVE: after READY, discover app-native LIVE navigation and reuse the proven HLS; do not bypass challenge/OTP/CAPTCHA.
3. Cloudflare: locate an already-authorized deployment path/connector or establish the minimal legitimate deployment credential. Do not weaken auth or put tokens in repository/logs.
4. TikTok: analyze the 30-environment matrix only after completion. Green variants close; if all fail, propose a different runtime/lower-memory first-party publisher rather than another identical GitHub-browser matrix.
