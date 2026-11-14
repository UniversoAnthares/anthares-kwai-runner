# Native TikTok LIVE browser control — authenticated cloud probe
STATUS: PARTIAL / NATIVE_BROWSER_CONTROL_NOT_FOUND
DATE: 2026-11-11
AREA: tiktok-live-native-browser
RUN_INITIAL: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43026188354
RUN_DIAGNOSTIC: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43026499727
JOB_DIAGNOSTIC: 130542426923
BRANCH: feature/tiktok-live-authorized-cloud-20261110

## Procedure
- Reused stored Playwright state for @lucasrosalem4 in GitHub secret; did not export cookies or identities. The state was loaded successfully in the GitHub-hosted Chromium process. Loading stored state does not alone prove server-side authorization; distinguish from rendered account navigation.
- Tested https://www.tiktok.com/tiktokstudio, https://livecenter.tiktok.com/, and https://seller-br.tiktok.com/ under the same in-memory browser context. Read-only: no LIVE initiated, no Restream changes, no mouse/keyboard interaction with the owner's PC.
- TikTok Studio rendered a real application with about 15,000 visible text characters and 58 visible controls. No desktop Go LIVE button, camera selector, Shop LIVE Manager link or practice mode exposed.
- TikTok LIVE Center rendered about 1,388 visible characters and 17 visible controls. LIVE Studio download hint present. No browser-based Go LIVE/camera/practice control.
- Seller Brazil redirected to /account/register; 3,504 visible characters, 13 controls. This is a seller account registration route, not an accessible TikTok Shop LIVE Manager. The public official help documents LIVE Manager specifically under Seller Center > LIVE & Video > LIVE Manager.
- Separate GitHub Chromium local getUserMedia test with simulated camera and microphone succeeded with one video track, one audio track, video 640x480; no account or broadcaster was connected to the device test.
- Workflow finished SUCCESS. No actual native LIVE, media injection into TikTok, or replacement of existing Restream broadcast occurred.

## Interpretation
- Cloud browser audio/video capture is technically supported. Access to native browser LIVE controls for this account has not been demonstrated.
- LIVE Manager official documentation applies to TikTok Shop creators/sellers and is not necessarily available for a non-Shop literary LIVE account. Seller Center shows account registration and has no manager here.
- Existing TikTok LIVE Studio is a distinct native Windows application requiring an eligible account and persistent Windows execution environment. It was not installed or launched.
- Do not bypass TikTok account eligibility, disguise prerecorded video as real-time human appearance, or disable the stable Restream/Hostinger broadcaster.

## Next gate
Only if TikTok presents an authorized native browser LIVE/Practice button for this account should the team test a declared prerecorded stream delivered as a virtual camera and separate audio track. Otherwise current tested Restream integration remains the functional cloud path.
OFFICIAL_DOC: https://seller-br.tiktok.com/university/essay?default_language=pt-BR&knowledge_id=6821109446412048