# TikTok official Content Posting API implementation prepared
STATUS: PARTIAL
DATE: 2026-10-06
AREA: tiktok

Implemented a causally different supported route:
- tiktok_official_api.py: creator_info/query read-only gate and refresh-token client; token values are never printed.
- .github/workflows/tiktok-official-api-readonly.yml: isolated read-only creator-info gate.

Official contract used:
- POST /v2/post/publish/creator_info/query/ requires video.publish.
- POST /v2/oauth/token/ refresh_token rotates access tokens.
- Direct Post can only follow successful creator-info and user authorization; no publish is attempted by this gate.

CURRENT EXTERNAL BOUNDARY:
No Anthares TikTok developer app/client credential or video.publish grant has been proven. Metricool is connected to a different TikTok identity (lucasrosalem4), not the expected universo.anthares, so it must NOT be used as a substitute.

NEXT LEGITIMATE ACTION:
Register/configure or identify the TikTok developer app, approve video.publish, and authorize the expected account once. Then set the resulting server-side credential/token secret and run the read-only gate. Do not return to cookie/browser environment matrices.
