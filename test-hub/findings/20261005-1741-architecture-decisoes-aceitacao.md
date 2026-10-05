# Decisões arquiteturais e critérios de aceitação consolidados
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Registrar limites arquiteturais e critérios finais para impedir regressões entre chats simultâneos.

## Resultado
Arquitetura operacional consolidada: execução 100% remota/cloud, PC desligado, custo R$0 sem billing/cartão. TikTok fica restrito a cortes; TikTok LIVE está fora. Kwai inclui cortes e LIVE de 6h; LIVE de 12h foi abandonada.

## Evidência decisiva
Decisões consolidadas durante a implementação e aceitas como requisitos do projeto. GitHub Actions público é o executor Android descartável escolhido; Cloudflare anthares-control é o plano de controle central.

## Consequência
Não reintroduzir PC/MEmu/ADB local como executor, Oracle/Ampere, Google Cloud que exija billing, Kuaishou Open Platform como publicador do Kwai brasileiro, CutMotions, cp.kwai.com antigo, Kwai Studio para posts comuns, aquisição Play Store/Aurora/goopdl como rota principal, APK não confiável ou túnel/VNC público como controle operacional.

Critérios de aceitação: login só fecha com sessão autenticada comprovada; corte Kwai/TikTok só fecha com post novo confirmado na conta correta e estado central concluído; LIVE Kwai só fecha com transmissão real de 6h; retry não pode gerar duplicata e estado uncertain deve bloquear repost cego.
