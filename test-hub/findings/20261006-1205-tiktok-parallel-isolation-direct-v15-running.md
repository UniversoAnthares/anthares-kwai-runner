# TikTok parallel failure isolation and direct replacement
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37456223265
SUPERSEDES: test-hub/findings/20261006-1135-lease-tiktok-v14-harness-repair.md

Run 37455600246 executed 15 simultaneous valid OIDC probes. Both protected endpoints returned HTTP success, but all replicas found Render session_bootstrapped=false. Run 37455687941 proved central session available=true with 21 cookies while Render restore returned control_http_error. Run 37455939291 expanded to 30 replicas and reproduced CONTROL_HTTP=200 / RENDER_HTTP=200 with Render state still not bootstrapped.

Causal replacement: tiktok_direct_canary_v15.py and the allowlisted tiktok-real-publish workflow now keep the central session on the GitHub runner and eliminate Render from the publication executor. Current run 37456223265 performs 15 parallel central-session probes followed by exactly one fenced direct canary. No simultaneous irreversible publication attempts.
