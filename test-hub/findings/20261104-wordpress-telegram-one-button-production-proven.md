# Telegram do fórum — botão único em produção
STATUS: PROVEN
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: ARA read-only/SSH WP-CLI, PHP 8.5, authenticated Hostinger
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/220
COMMIT: 88aa5b6a97c2de043fb352a9621fc60fe0e0d9b7
SUPERSEDES: test-hub/findings/20261104-telegram-wordpress-production-lease.md

## Diagnóstico
O plugin ativo na Hostinger continha a versão antiga do Telegram (SHA-256 php eaa1f10895f52a22405d574f0febe24b877dd32664255fcd5ae5e0165a74a483, JS 451712d499e5de71b08d730bc914698d1af3b637cc759101e117ec67705bd220, CSS a45b72a7b9ecb5602a385323dfef337dcbef32323137331045be0c6c9477727e). A PR corrigida ainda não havia sido mesclada nem implantada. Build Railway do relay é problema separado.

## Prova antes da implantação
PR #220 branch 9930f41e3cc6bb9ff6d558aa80407ec554644fba, 5 arquivos (PHP, JS, CSS, dois manifests). Manifest preflight executado em worktree efêmero de Hostinger: PASS 605/605 auditable assigned, exactly once. Lint PHP 8.5: PASS. JavaScript toggle click-click-Escape: PASS; sem postagem Telegram de teste.

## Implantação
PR #220 integrada via squash em main SHA 88aa5b6a97c2de043fb352a9621fc60fe0e0d9b7. Fonte recuperada por Git autenticado já existente na Hostinger; sem upload pelo PC ou alteração do checkout com arquivos QA modificados por outro agente. Copia prévia dos três arquivos em backup privado com permissão 700. Implantação atômica de apenas três arquivos do plugin, condicionada à checagem exata de SHA-256 anterior; rollback preparado. Após implantação os git blobs coincidem com PR: PHP 6c2c0f4b8ad81b1c2941071b2718df9b054b09eb; JS f278b3bfa8ab4ceaa2db249bd0513a24899e2f56; CSS 761b27e2f8cdb501b3de06834d293990048de361. Sem resíduos de arquivos .deploy-*.

## Validação real
WP-CLI com WordPress carregado executou função anthares_telegram_usuario_render no contexto fórum, tópico 10898: BUTTON_EXACT PASS, PANEL_HIDDEN PASS, TOPIC_LINK PASS, ARIA_EXPANDED PASS. PHP lint PASS. JS/CSS acessíveis externamente via anthares.us com HTTP 200 e git blob exato aprovado na PR. Controle fechado ocupa apenas botão "Enviar para o canal no Telegram"; clique mostra campo/opções/explicação.

## Limites
Somente interface e compartilhamento manual são comprovados; a funcionalidade MTProto de enviar pelo próprio Telegram ainda depende do relay Railway (último deploy FAILED, PR relay #5 aberta). Não foi efetuado envio real, login Telegram, cobrança, novo projeto, volume nem alteração na Railway. O backup privado permanece disponível. Lease encerrado. Uma futura ação no relay exige preflight independente e confirmação de custo zero.
