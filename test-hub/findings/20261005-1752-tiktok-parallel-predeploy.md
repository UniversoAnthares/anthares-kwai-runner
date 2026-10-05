# TikTok parallel diagnostics antes do deploy Render
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37372730568
JOB: 111973641491, 111973641523, 111973641474
COMMIT: d3a082b4
SUPERSEDES: none

## Objetivo
Isolar em paralelo runner, Render, sessão, identidade, mídia e dry-runs do publicador TikTok.

## Resultado
Dois probes produziram evidência positiva: 03 Render health/revision e 06 MP4 cloud accessibility. O probe 04 falhou com HTTP 401 em /session-status. Os demais foram cancelados e não constituem evidência negativa das hipóteses.

## Evidência decisiva
Job 111973641523 concluiu success para Render health/revision. Job 111973641491 concluiu success para MP4 cloud accessibility. Job 111973641474 recebeu urllib.error.HTTPError: HTTP Error 401: Unauthorized. Investigação posterior mostrou autoDeploy=no no serviço Render e revisão antiga em produção.

## Consequência
Preservar 03 e 06 como comprovados. Não repetir esses probes sem necessidade. Não classificar sessão, identidade ou dry-run como FAILED por esta rodada. Reexecutar apenas os probes dependentes de OIDC depois do deploy explícito da revisão que autoriza o repositório público.
