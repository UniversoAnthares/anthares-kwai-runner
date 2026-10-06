# QA: TikTok approved rehydrate proves session and identity; blocker is media secret only
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37395199814
JOB: 112049403343
COMMIT: 27924afac0aef0096b29390d31fbccfb627395fb
SUPERSEDES: test-hub/findings/20261005-2040-qa-tiktok-rehydrate-control-oidc-invalid.md

## Resultado
A reidratação aprovada funcionou até a prova de identidade: bootstrap Render HTTP 200 com 21 cookies, session-status bootstrapped=true, session-test HTTP 200 ok=true identity_verified=true e persistência central HTTP 200. O job só falhou no último config-status porque ANTHARES_VIDEO_SECRET=false.

## Evidência decisiva
RENDER_OIDC_BOOTSTRAP=OK; RENDER_SESSION_STATUS=OK; RENDER_SESSION_TEST=OK identity_verified=true; CENTRAL_SESSION_PERSIST=OK. Config-status: ANTHARES_VIDEO_ENDPOINT=true, EXPECTED_TIKTOK_USERNAME=true, EXPECTED_TIKTOK_USER_ID=true, ANTHARES_VIDEO_SECRET=false.

## Consequência
Sessão e identidade TikTok no Render agora estão PROVEN; não repetir login/rehydrate. O único blocker observado neste job é configuração de mídia/secret. Resolver o contrato de fonte de vídeo sem expor segredo e então executar readiness/publish canary com verificação independente.