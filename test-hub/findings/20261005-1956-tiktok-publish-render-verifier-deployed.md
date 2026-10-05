# TikTok publisher verificador implantado no Render
STATUS: PROVEN
AREA: tiktok-publish
DATE: 2026-10-05
RUN: Render deploy dep-db23hdflot8c73dmndn0
JOB: none
COMMIT: 2eb0d9bfabf60e3e597fa46a6c7f58a9e4c10c79
SUPERSEDES: test-hub/findings/20261005-1955-chat3-tiktok-publish-render-deploy-lease.md

BASELINE_PROVEN: main do anthares-clipper contém confirmation_evidence fail-closed e verificação pós-publicação por único ID novo do perfil; canário real continua bloqueado por tiktok-session; live anterior estava em 1917fb3579693b2725658e004fcb109a75b7af76.
FAILED_AVOIDED: deploy não executou /publish; restore 403/env-seed não foi repetido; nenhuma mutação Cloudflare; health não foi interpretado como prova de publicação.
SUCCESS_SIGNAL: Render live exatamente em 2eb0d9bfabf60e3e597fa46a6c7f58a9e4c10c79, build concluído, health do novo instance 200 e zero logs /publish durante o deploy.
FAILURE_SIGNAL: revisão diferente, deploy falho ou publicação inesperada.
TEST_VALIDITY: Render API retornou deploy dep-db23hdflot8c73dmndn0 status live, finishedAt 2026-10-05T23:56:11.141681Z; logs mostraram build successful e GET /health 200; consulta de logs path=/publish entre 23:54:20Z e 23:57:30Z retornou vazio. Isto prova deployment readiness, sem equivaler a publicação TikTok real.

## Objetivo
Levar ao executor remoto o publisher com prova pós-publicação forte sem disparar canário enquanto a sessão segue indisponível.

## Resultado
PROVEN. O serviço anthares-tiktok-render-rootless agora está live no commit 2eb0d9bfabf60e3e597fa46a6c7f58a9e4c10c79. O publisher disponível no executor exige inventário pré/pós do perfil, exatamente um novo video ID, concordância com a URL pós-publicação quando ela expõe ID e envia remote_id real ao ledger.

## Consequência
LEASE tiktok-publish encerrado. A cadeia de publicação está pronta no executor até o ponto imediatamente anterior ao canário. Próxima causa exclusiva: tiktok-session/control plane. Quando o endpoint central de sessão ou fonte remota equivalente ficar PROVEN, reacquirir tiktok-session, validar universo.anthares e só então executar um canário real.
