# CLOSED — TikTok Render central rehydrate after Cloudflare v12
STATUS: PRODUCTION PROVEN — superseded by completed prepublish proof
AREA: tiktok-session
DATE: 2026-10-05
OWNER: CHAT 5

ORIGINAL_BASELINE: production Cloudflare v12 had returned HTTP 200 + available=true + 21 cookies to run 37394495580.

FINAL_PROOF: run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396243429 completed the production session path and proved:
- central TikTok session GET HTTP 200, available=true, 21 cookies;
- Render bootstrap HTTP 200 with 21 cookies;
- Render `/session-test` HTTP 200 with worker_code=0 and identity_verified=true;
- refreshed 21-cookie state persisted centrally HTTP 200;
- direct Render `/publish-dry-run` HTTP 200 with ok=true, identity_verified=true, upload_page_auth=true;
- no publish endpoint was called by this proof.

ACCOUNT: `universo.anthares`; expected user ID 7577123938226406401.

RESULT: the tiktok-session dependency that this lease tracked is closed. The remaining canary/media work is owned by the separate `tiktok-canary-media` lease and must not be duplicated here.
