# TikTok Render persistent session diagnostic
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-06
RUN: Render service logs
JOB: srv-db18d3tg1s2s7391l4ng
COMMIT: none
SUPERSEDES: none

## Objetivo
Diagnosticar read-only o executor persistente Render sem competir com publicação/sessão em mutação.

## Resultado
O serviço anthares-tiktok-render-rootless está live e responde /health e /config-status com HTTP 200. O endpoint local /session-status também responde HTTP 200, porém seu diagnóstico interno registra SESSION_STATUS_SAFE={http:403, reason:control_http_error}. Isso localiza uma fronteira adicional: a checagem de sessão do Render está sendo impedida pela chamada ao control plane, antes de poder provar upload autenticado. Nenhum cookie/token foi lido ou registrado.

## Evidência decisiva
Render logs em 2026-10-06 11:20:04Z e 11:22:19Z: GET /session-status HTTP/1.1 200; SESSION_STATUS_SAFE http=403 reason=control_http_error. Serviço srv-db18d3tg1s2s7391l4ng permanece live.

## Consequência
Agente TikTok deve preservar a classificação env30 (TikTok rejeita sessão web restaurada) e, na cadeia Render, corrigir primeiro a autorização Render -> control plane para /session-status. Depois repetir somente /session-status/read-only upload-access. Não disparar publish até essa prova. Esta observação é independente e não autoriza substituir o lease ativo.
