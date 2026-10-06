# TikTok 15-way session boundary — environment-dependent auth
STATUS: PROVEN
AREA: tiktok-session-boundary
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37418745200
RELATED: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37418647980

## Test validity
Fifteen independent GitHub-hosted browser replicas loaded the same central session through authenticated OIDC. Cookie diagnostics showed stable auth-cookie material, including matching sessionid/sessionid_ss hashes across inspected replicas.

## Result
Most inspected replicas redirected /upload to /login, while at least replica 15 reached https://www.tiktok.com/upload directly with the same central session material. Separately, central-session probe 37418647980 rehydrated 21 cookies into Render and proved identity_verified=true plus upload_page_auth=true and direct publisher dry-run OK.

## Classification
The stored central TikTok session is not globally expired or unusable. Authentication acceptance is environment/intermittency dependent between browser executions. Do not rotate credentials solely because GitHub-hosted replicas redirect. Prefer the already-proven Render browser path for the serialized production canary.

## Safety
This matrix is read-only and does not prove a real post. Exactly one irreversible publication attempt remains required, with publication_started, independent verification, remote_id and confirmed ledger evidence.