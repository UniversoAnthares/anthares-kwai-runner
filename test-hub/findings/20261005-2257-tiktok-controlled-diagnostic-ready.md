# TikTok controlado instrumentado para diagnóstico de distribuição
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: 6255bf4189653155516947861ccd7288bcad52b7
SUPERSEDES: none

## Objetivo
Executar poucos posts TikTok comparáveis e isolar a variável responsável pela distribuição anormal.

## Resultado
O workflow passou a tratar 3/dia como limite autoritativo mesmo enquanto o Worker implantado ainda reporta remaining legado de 100/dia. Antes da publicação ele grava manifesto diagnóstico com SHA-256 do MP4, source/segment/start/end, rota, target e ffprobe de duração/bitrate/codecs/resolução/FPS. O manifesto entra nos artifacts de falha. Isso fecha a instrumentação necessária para comparar arquivo/renderização/rota sem confundir variáveis.

A publicação real controlada ainda depende de uma execução do pipeline remoto que consiga chegar ao publisher. O repositório privado continua com falha imediata de runner registrada no hub; não foi repetido como se fosse teste de distribuição.

## Evidência decisiva
Commit 6255bf4 remove a dependência lógica do remaining=100-count para o limite experimental e adiciona Capture controlled TikTok diagnostic manifest antes do publisher.

## Consequência
Manter 3/dia e 3-6h. O próximo post real gera evidência reproduzível para distinguir mídia/encoding de rota de upload. Não atribuir causa ao algoritmo/cadência antes de views observadas.
