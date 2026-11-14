# TikTok LIVE — câmera e microfone virtuais em Chromium GitHub
STATUS: PROVEN
AREA: tiktok-live-browser-media
DATE: 2026-11-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42865993013
JOB: 130004343558
COMMIT: 7b5361b6a37d29b3e1bcd63f5dfb1386ee6a3130
SUPERSEDES: test-hub/findings/20261110-tiktok-live-browser-media-smoke-running.md
LEASE_AREA: tiktok-live-browser-media
LEASE_STATUS: CLOSED

## Resultado
A execução GitHub Ubuntu terminou SUCCESS com marcadores CLOUD_BROWSER_MEDIA_TOOLS_READY=1 e CLOUD_BROWSER_MEDIA_SMOKE_OK=1. Prova do navegador: CLOUD_BROWSER_MEDIA_TRACKS={"active":true,"audio":["live"],"height":640,"video":["live"],"width":360}.
A origem foi HLS Anthares com amostra local efêmera de quatro segundos e identificação visual de programa gravado. Firefox/Chrome user desktop, Android ou RTMP externo não participaram da transmissão.

## Limite preciso
O Chromium leu fontes de mídia virtuais em uma página HTML de teste localhost. A aplicação não entrou em TikTok, não publicou, não confirmou elegibilidade da conta, não criou sala e não transmitiu a espectadores. Os controles de iniciar LIVE estavam ausentes na inspeção autenticada de @lucasrosalem4 (run 42863880530). A sessão de @universo.anthares retornou 401 na tentativa de leitura OIDC autorizada (run 42864768551); nenhum contorno foi tentado. Câmera virtual não concede permissão LIVE nem transforma o TikTok Studio comum em uma interface de broadcast.

## Consequência
Código e teste de mídia virtual na branch isolada / PR #2301; produção permanece desativada até existir uma interface LIVE oficial efetivamente disponível e o uso de gravações estar permitido. Não inventar resultados ou conferir PROVEN de transmissão TikTok.
