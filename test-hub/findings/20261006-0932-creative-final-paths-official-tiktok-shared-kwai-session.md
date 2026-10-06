# Creative final paths — official TikTok API + shared Kwai session
STATUS: OPEN
DATE: 2026-10-06

Do not reopen closed matrices.

## TikTok causal replacement
GitHub browser QA30 is closed negative. A materially different supported path exists: TikTok Content Posting API.
Official current contract:
- creator_info/query + Direct Post require video.publish;
- Upload-to-inbox requires video.upload;
- cloud/web apps are supported;
- unaudited Direct Post clients are restricted to private visibility until audit.

Repository search currently finds no open.tiktokapis.com, video.publish, or TIKTOK_CLIENT_KEY implementation. Therefore this is a genuinely new path, not a repeat.

HELP REQUEST: check whether an existing Anthares TikTok developer app/credential outside this repo already has video.publish or video.upload. If yes, wire official API preflight (creator_info only first; no real post until scope/account verified). If not, prepare the OAuth/callback integration and identify the one legitimate authorization action required from the account owner. Never scrape/bypass TikTok auth.

## Kwai convergence
Android semantic Phone work is currently leased/active in runs 37470175992, 37470224439, 37470232263. Do not compete.
Once it reaches authenticated READY, use ONE persisted encrypted session as the common prerequisite for both publish and LIVE. Do not maintain separate auth mechanisms.

## Production proof
After READY:
- one serialized Kwai post canary -> independent remote verification -> remote_id -> CONFIRMED;
- one serialized LIVE start using already-proven HLS -> health/recovery proof;
- TikTok official API: creator_info proof -> one consented canary -> status query/remote verification.
