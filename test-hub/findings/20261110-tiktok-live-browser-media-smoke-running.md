# TikTok LIVE — teste de câmera/microfone no navegador hospedado
STATUS: RUNNING
AREA: tiktok-live-browser-media
DATE: 2026-11-10
OWNER: chatgpt-tiktok-live-20261110-remote-device
LEASE_AREA: tiktok-live-browser-media
LEASE_EXPIRES: 2026-11-10T22:30:00Z
RUN: pending
JOB: none
COMMIT: f334dddd7a0b2409f3cfcc8322762fbf93dd323b
BASELINE_PROVEN: FFmpeg hosted run 42853860337 succeeded. TikTok secondary account read-only access run 42863880530 reached LIVE Producer but no Go LIVE or RTMP visible. Primary OIDC session read returned HTTP401 in run 42864768551 (do not bypass).
FAILED_AVOIDED: No TikTok website action, no LIVE publishing, no account mutation, no computer/Android as broadcaster, no emulated identity or auth bypass. Browser fake media is tested only against local mock getUserMedia() on ephemeral GitHub Actions.
SUCCESS_SIGNAL: Browser Chromium captures frame and audio track sourced from 4-second HLS sample, outputs CLOUD_BROWSER_MEDIA_SMOKE_OK=1; hosted job succeeds.
FAILURE_SIGNAL: missing media devices, missing HLS, ffmpeg encoding fails, Chromium getUserMedia failure; report exact nonsecret code.
TEST_VALIDITY: proves only virtual camera/microphone media delivery within cloud browser, never LIVE eligibility or TikTok broadcasting. Source is prerecorded and intended to be disclosed when used in a platform accepting it.
