# Round update: new mechanisms executed
STATUS: RUNNING
DATE: 2026-10-06

## TikTok
- Built and deployed an ultralean Render publication path: 800x600 viewport, nonessential image/font/media request blocking, one renderer, reduced Chromium features, tiny 5s 540x960 owned canary, external profile reconciliation.
- Render deployment of current ultralean worker is live.
- v14 GitHub control workflow reached OIDC generation but protected queue call still returned HTTP 401. Current control source contains tiktok-real-publish.yml allowlist and was redeployed twice; therefore the next diagnostic is exact JWT claim-vs-deployed-verifier comparison, not another irreversible publish.
- No v14 publication_started occurred; no duplicate risk introduced.

## Kwai
- Pivoted from the non-clickable APK Phone composite to official Kwai Studio login surface.
- First Android attempt proved the blocker was Chrome first-run experience, not Kwai Studio itself.
- A second workflow is running with deterministic Chrome FRE handling plus 15 observations.
- Existing APK path still proves MAIN -> Log in -> chooser with Phone visible.

## Safety
No new irreversible publication occurred in this round yet. Existing v13 remains independently confirmed absent/reconciled. All new publication attempts remain behind exact lease + publication_started + independent confirmation gates.
