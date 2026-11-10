# TikTok Android official download site — app-attribution redirect
STATUS: PARTIAL
AREA: tiktok-live-first-party-official-apk
DATE: 2026-11-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42873637165
JOB: 130031067108
COMMIT: 0f285504290cce3bbc4582414fe2aa239c4c0d47
SUPERSEDES: test-hub/findings/20261110-tiktok-first-party-apk-readonly-running.md
LEASE_AREA: tiktok-live-first-party-official-apk
LEASE_STATUS: CLOSED

## Evidence
- Official TikTok website https://www.tiktok.com/download in mobile Chromium launched from GitHub Ubuntu Actions.
- Run 42873089373 initially failed to reach DOMContentLoaded (TIMEOUTERROR). After switching to navigation response commit, run 42873388181 reached HTTP200 on a redirect outside *.tiktok.com.
- Diagnostic run 42873637165: TIKTOK_APK_FIRST_PARTY_PAGE_HTTP=200; TIKTOK_APK_FIRST_PARTY_DOMAIN_OK=false; TIKTOK_APK_REDIRECT_HOST=snssdk1233.onelink.me; TIKTOK_APK_PROBE=OFFICIAL_PAGE_UNAVAILABLE.
- The destination is an app attribution/link-routing host. The probe intentionally did not follow the cross-domain redirect to install APK or treat a tracking link as verified APK distribution. No package downloaded.
- Separately, run 42872343720 proved Google Play in ephemeral Android requires a signed-in Google account: TIKTOK_GOOGLE_PLAY_OUTCOME=GOOGLE_ACCOUNT_REQUIRED.
- None of the tests started TikTok LIVE, authenticated an Android TikTok account, touched the owner's device, uploaded media or changed Kwai workflows.

## Conclusion
The corrected Play Store UI diagnosis eliminated the previous uncertain wait: Google account sign-in is a real external dependency. TikTok official /download mobile path did not deliver an APK directly in the tested hosted browser and redirected to snssdk1233.onelink.me. Neither route currently provides a remotely authenticated native TikTok app or LIVE start control. Cloud FFmpeg/HLS and virtual camera media tests remain independently PROVEN (42853860337 / 42865993013).
Keep PR #2301 draft, publish automation disabled, and avoid repeated denied/unchanged routes. Any later route must use an officially supported app installer and LIVE-account authorization with independent viewer proof.
