# Lease — CORTES content cycle + partial remote extraction
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-15
RUN: none
JOB: none
COMMIT: baseline 3e51eaaae2adc8705c5c1a5f7bd1739605bf3b16
SUPERSEDES: none

## Objetivo
Implementar a política diária de fonte única, fallback lives→vídeos comuns >15 min→lives, retenção até confirmação multi-rede e seleção de no máximo 4 masters longos/dia fora do YouTube; depois comprovar um corte real por transferência parcial do YouTube processado em runner remoto. Não publicar.

## BASELINE_PROVEN
O CORTES existente mantém uma única live bloqueadora e o despachante conserva o arquivo até as redes ativas confirmarem. A política obrigatória do Anthares exige masters curtos 30–90 s e longos 5–14 min com microcortes.

## FAILED_AVOIDED
Não usar Android virtual como publicador, não tocar nos publicadores Kwai comprovados, não depender de Render/TinyFish/Browserless/CircleCI. O teste de mídia usará GitHub-hosted runner somente para extração/processamento e não publicará.

## SUCCESS_SIGNAL
1. Testes unitários da nova máquina de estados passam; 2. fonte diária é única; 3. fallback exclui Shorts e vídeos <=15 min e nunca envia esses cortes ao YouTube; 4. corte só fica deletável após confirmação de todos os destinos e verificação final; 5. se houver >3 longos fora do YouTube, somente 4 são elegíveis e o último slot é 22:00, preservando microcortes; 6. workflow remoto gera MP4 real a partir de seção parcial do YouTube e publica artefato, sem publicação social.

## FAILURE_SIGNAL
Qualquer violação dos invariantes acima; download integral da live no teste parcial; publicação social; ou workflow sem MP4 verificável.

## TEST_VALIDITY
Falha de autenticação/anti-bot do YouTube ou indisponibilidade do runner invalida o teste de extração e não refuta a arquitetura. Método de download integral de redundância fica explicitamente fora desta rodada.

## Expiração
2026-10-15T15:49:00Z
