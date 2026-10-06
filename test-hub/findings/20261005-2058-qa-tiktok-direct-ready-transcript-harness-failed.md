# QA: TikTok direct publisher ready; transcript failure is source-harness only
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396243429 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396595992
JOB: 112052775983 ; 112053951188
COMMIT: 0351baefd6b0a62cd293f742a56d29debfc330e5
SUPERSEDES: none

## Resultado
O prepublish direto está PROVEN: sessão/identidade, upload_page_auth, queue-health e dedupe passaram; a descoberta de cinco fontes próprias também passou. O transcript-analysis posterior falhou apenas porque yt-dlp no runner recebeu o anti-bot do YouTube antes de baixar legendas. Isso não é falha do publisher nem da fonte em si.

## Evidência decisiva
37396243429: RENDER_DIRECT_PUBLISHER_DRYRUN=OK identity_verified=true upload_page_auth=true; TIKTOK_QUEUE_PREFLIGHT=OK dedupe_healthy=true; ANTHARES_OWNED_SOURCE_DISCOVERY=OK. 37396595992: `Sign in to confirm you’re not a bot` durante yt-dlp de subtitles, antes de qualquer análise/transcrição.

## Consequência
Não repetir yt-dlp anônimo do GitHub como se fosse teste de publicação. A seleção de mídia deve usar um caminho causal diferente (endpoint/fonte já controlada, transcript API autenticada, ou outra aquisição remota) e então canário real com verificação independente.