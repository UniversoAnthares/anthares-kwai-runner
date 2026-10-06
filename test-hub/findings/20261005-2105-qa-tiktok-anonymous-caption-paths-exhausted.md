# QA: anonymous caption paths exhausted for current TikTok canary source
STATUS: FAILED
AREA: tiktok
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396595992 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396889644 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37397063482
JOB: 112053951188 ; 112054880803 ; 112055429687
COMMIT: a6a00d53e52ddf03891392acacb17e09890ddc06
SUPERSEDES: none

## Resultado
Três famílias anônimas independentes não entregaram legenda utilizável para o vídeo canário: yt-dlp foi bloqueado por anti-bot; timedtext direto retornou HTTP 200 com corpo vazio e watch HTML sem captionTracks; Invidious listou Portuguese auto-generated mas o track retornou 0 bytes e as demais instâncias falharam HTTP.

## Evidência decisiva
37396595992: `Sign in to confirm you’re not a bot`. 37396889644: todos timedtext bytes=0, CAPTION_BASEURL_COUNT=0. 37397063482: inv.nadeko listou captions mas pt track bytes=0; demais proxies list_error HTTPError.

## Consequência
Não abrir novas matrizes de captions anônimas equivalentes. Para o canário, usar fonte/mídia controlada já disponível sem depender de transcript, ou aquisição autenticada/servidor próprio com mudança causal. Isto não reduz o estado PROVEN do publisher direto.