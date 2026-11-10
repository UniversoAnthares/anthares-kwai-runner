# TikTok LIVE — executor externo e autorizado (preparação)

Conta e chave de transmissão dependem da autorização real do TikTok.
Nenhuma chave é gerada, adivinhada ou obtida por API privada. Vídeos gravados
recebem identificação persistente na imagem: `PROGRAMA GRAVADO`.

## O que está implementado
- Preflight read-only do HLS de origem e da disponibilidade do FFmpeg.
- Codificação 720x1280 com áudio AAC, via FFmpeg, inteiramente no GitHub Actions.
- Prova real do executor: Actions run #42853533867, job 129960318578; `ANTHARES_CLOUD_FFMPEG_READY=1`, `ANTHARES_HLS_PREFLIGHT_OK=1` e `ANTHARES_DRY_ENCODE_OK=1` (8 segundos; sem envio).
- Transmissão manual protegida por TRÊS condições independentes:
  1. variável `TIKTOK_LIVE_ACCOUNT_AUTHORIZED=true`, somente após elegibilidade validada;
  2. variável `TIKTOK_LIVE_PRERECORDED_APPROVED=true`, somente quando o formato estiver autorizado;
  3. secret `TIKTOK_LIVE_RTMP_DESTINATION` com endereço real fornecido pelo TikTok.
- GitHub Actions aceita somente canários autorizados de 15 a 600 segundos, limite do job 20 minutos. O limite rígido do runner hospedado é de 6 horas; a transmissão contínua deve usar um executor persistente externo com lease e monitoramento.
- Sem agendamento de transmissões e sem alterações no controlador Kwai.
- Saída do FFmpeg suprimida para evitar exposição da chave.

## Pendências para ativação
- Verificação da autorização da conta e da política vigente para programação gravada.
- Chave RTMP fornecida oficialmente para cada sessão e duração permitida.
- Confirmação externa de recepção do vídeo pelo TikTok (FFmpeg terminar não prova LIVE).
- Só depois de validar: controlador de renovações, com estado idempotente e healthcheck.

## Teste
O push da branch instala FFmpeg, verifica HLS e executa 8 segundos de codificação `null` (sem envio ao TikTok).
A execução de transmissão exige dispatch explícito com `transmit=true`.
