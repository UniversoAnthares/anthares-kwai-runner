# TikTok official API credential discovery — read-only
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-06
RUN: none
JOB: Gmail + repository read-only probes
COMMIT: none
SUPERSEDES: none

## Objetivo
Avançar o caminho causal novo Content Posting API sem interferir no lease de tiktok-publish/session.

## Resultado
Repository search confirms no official Content Posting API implementation. Gmail search for TikTok developer/client/API material found no developer-app registration/approval mail; only account verification and project CI notifications were present. A broad local filesystem search was invalid because the remote websocket closed before completion and must not be treated as evidence.

## Evidência decisiva
Repo contains no open.tiktokapis.com/video.publish/video.upload implementation. Gmail query for TikTok developer/client/app/API returned no TikTok developer onboarding/approval message.

## Consequência
Official API remains a valid new route, but no existing developer app credential has been proven. Next independent action is to inspect the TikTok developer portal/account for an existing app or create/configure one through the supported flow, then request video.publish/video.upload and run creator_info/query only. Preserve current browser-session findings; do not repeat env/UA/viewport matrices. No token/secret should enter Git or Hub.
