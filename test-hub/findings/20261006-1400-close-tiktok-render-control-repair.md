# Close lease — TikTok Render control authorization repair
STATUS: PARTIAL
AREA: tiktok-session
DATE: 2026-10-06
RUN: 37472086588
COMMIT: 9ca62651b0c789fbe94e42c588b1eb8f8df4cf84
SUPERSEDES: 20261006-1350-lease-tiktok-render-control-repair.md

The read-only broker path resolved the previous control-plane authorization boundary: central state read 200, Render bootstrap 200 with 21 cookies, session-status 200 and bootstrapped=true. Identity verification timed out with HTTP 504 and identity_verified=false. Lease closed without publication. Next mutation requires legitimate owner session/OAuth authorization.
