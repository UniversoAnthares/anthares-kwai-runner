# Telegram WordPress — lease do encaminhamento manual
STATUS: RUNNING
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: none
JOB: ChatGPT continuation
COMMIT: anthares-wordpress main 6a76d0f62d9dcb5544609906a3e222ea20929690
SUPERSEDES: test-hub/findings/20261104-wordpress-telegram-one-button-production-proven.md

## Baseline PROVEN
O botão fechado do Telegram está comprovado em produção. O caminho manual atual abre o preview público t.me/universoanthares00, sem prefill. A vinculação MTProto depende de relay Railway offline.

## Objetivo
Corrigir somente o fluxo manual do plugin: abrir chat público com texto preparado pelo deep link Telegram oficial, manter alternativa Web e texto obrigatório.

## FAILED_AVOIDED
Não tentar entrega automática, deploy Railway/custos, outra integração, envio real, nem promover GitLab divergente. Preservar grupo @universoanthares00.

## SUCCESS_SIGNAL
JS gera tg://resolve com domain e text encodados; fallback Web abre o grupo e mantém cópia manual; PHP e JS válidos, toggling existente preservado.

## FAILURE_SIGNAL
Preview t.me genérico, texto vazio, URL de chat incorreta, novo custo ou colisão com outros agentes.

## TEST_VALIDITY
QA estático prova código; somente teste em aplicativo autenticado confirmará o rascunho. Sem postagem real neste lease.

## Lease
Owner ChatGPT. Start 2026-11-04T11:33:28.064Z; expires 2026-11-04T11:58:28.064Z; duration 25min. Encerramento append-only.
