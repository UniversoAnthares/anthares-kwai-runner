# WordPress Telegram — botão único e discreto
STATUS: RUNNING
AREA: wordpress-telegram
DATE: 2026-11-03
RUN: none
JOB: ChatGPT continuation, WP PR #220
COMMIT: ef5f3a081ceac1b01069a7e552af5c8e9c7556fc
SUPERSEDES: none

## Baseline
GitHub anthares-wordpress main HEAD 67271894671786a60e7f5eece9c7b2b8e30423a6, branch fix/telegram-share-20261103 HEAD ef5f3a081ceac1b01069a7e552af5c8e9c7556fc; PR #220 aberto. Conteúdo atual do target inspecionado: PHP 62cca22d8c1f3ec64fe824233f5ecaa75e2b6c7a, JS fad2c1b765dd3ee6ddc91374cec6b23650f60527, CSS 983b4734598822545609a12008ee2c8475cf8101. Main conserva interface antiga; GitLab peer main historicamente divergente e sem merge.

## Objetivo
Converter o painel Telegram em um botão único com texto exato “Enviar para o canal no Telegram”; clique expande formulário + instrução breve; clique seguinte recolhe. Corrigir apresentação em telas pequenas e preservar compartilhamento manual e vínculo existentes. QA estático e sintático, preflight antes de merge. Mutações apenas dos 3 targets no branch da PR #220; nenhum deploy ou publicação Telegram automática.

## Baseline/failed avoided
Retomar o código existente da PR #220 após releitura. Não duplicar serviço Telegram, não publicar no grupo em testes, não alterar outros componentes. Railway segue pendente. Principal risco: defeito de HTML/CSS que mantenha conteúdo visível quando hidden.

## Success signal
Uma única ação visível fechada, detalhes ausentes até clique, aria-expanded e aria-controls corretos, fechamento por clique/Escape, testes estáticos e sintaxe, SHA do branch controlado.

## Failure signal
Conteúdo exposto com hidden, foco inacessível, quebra do link do tópico, perda de ações, problema de PHP/JS/CSS.

## Test validity
Validar código isoladamente; somente deploy + teste no navegador comprova resultado em produção.

## Lease
wp telegram UI, 30 minutos a partir da criação. Encerrar por finding posterior append-only.
