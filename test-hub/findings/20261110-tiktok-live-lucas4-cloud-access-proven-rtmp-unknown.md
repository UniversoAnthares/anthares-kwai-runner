# TikTok LIVE — Lucas4 account cloud-readonly Studio access
STATUS: PARTIAL
AREA: tiktok-live-account-readonly
DATE: 2026-11-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42863880530
JOB: 129996922045
COMMIT: 677cd5b3a826df0185bb2a35237b68483a255194
SUPERSEDES: test-hub/findings/20261110-tiktok-live-readonly-eligibility-probe-running.md
LEASE_AREA: tiktok-live-account-readonly
LEASE_STATUS: CLOSED

## Resultado
- GitHub Ubuntu+Chromium terminou sucesso, secret de sessao de @lucasrosalem4 leu paginas oficiais sem publicar.
- TIKTOK_LIVE_STUDIO_PROBE: status=200, login_prompt=false, owner_media_links=true.
- TIKTOK_LIVE_PRODUCER_PROBE: status=200, login_prompt=false, producer_marker=true, rtmp_label_visible=false, live_action_visible=false.
- Resultado do programa: NO_RTMP_CONTROL_VISIBLE_ELIGIBILITY_UNKNOWN.
- Nenhum token/chave RTMP, room ou transmissao foi criado; nenhuma informacao sensivel foi impressa.

## Consequencia
Sessao navegavel e acesso à pagina LIVE comprovados. Elegibilidade RTMP continua desconhecida. A ausencia de controle RTMP visivel impede iniciar a LIVE; nenhum automatismo de publicacao deve ser habilitado. O resultado nao permite afirmar que a conta foi recusada pelo TikTok.
