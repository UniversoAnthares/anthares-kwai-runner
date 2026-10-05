# Render estava servindo revisão antiga; deploy manual concluído
STATUS: PROVEN
AREA: tiktok
DATE: 2026-10-05
RUN: none
JOB: Render deploy dep-db21j43tqb8s73bnhiug
COMMIT: 3a97abe11451e9c1ef877dfed83591251144fad1
SUPERSEDES: none

## Objetivo
Explicar os 401 observados nos diagnósticos TikTok do repositório público e colocar em produção a revisão que autoriza o public runner.

## Resultado
O serviço Render anthares-tiktok-render-rootless estava com Auto Deploy desligado. Alterações posteriores no GitHub não estavam chegando ao serviço. Foi disparado deploy manual pela API do Render e o deploy dep-db21j43tqb8s73bnhiug terminou com status live.

## Evidência decisiva
Na rodada 37372730568, os jobs 03 Render health/revision e 06 MP4 cloud accessibility passaram. O job 04 TikTok session persistence falhou com HTTP 401 em /session-status. A configuração do serviço mostrou autoDeploy=no. O deploy manual iniciado em 2026-10-05T21:41:36Z terminou live em 2026-10-05T21:43:06Z.

## Consequência
Não interpretar o 401 daquela rodada como falha da sessão TikTok. Ele foi produzido contra uma revisão antiga do serviço. Repetir somente os probes dependentes de autenticação após o deploy live; preservar como PROVEN que Render health e transporte de MP4 público já funcionam. Enquanto Auto Deploy permanecer desligado, toda alteração do worker Render exige deploy explícito antes do teste.
