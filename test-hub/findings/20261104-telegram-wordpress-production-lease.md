# WordPress Telegram — finalizar interface e implantação
STATUS: RUNNING
AREA: wordpress-telegram + wordpress-qa-manifest-scoped
DATE: 2026-11-04
RUN: none
JOB: ChatGPT current user request
COMMIT: WordPress PR #220 head 326f24bc36a51fd07a02e71b2f863f31a93f9f6b
SUPERSEDES: none

## Preflight
WordPress main observado 179b49847c0441b04680abcbfab6d09482f42b31 (pode avançar); plugin em produção Hostinger SHA256 PHP eaa1f10895f52a22405d574f0febe24b877dd32664255fcd5ae5e0165a74a483, JS 451712d499e5de71b08d730bc914698d1af3b637cc759101e117ec67705bd220, CSS a45b72a7b9ecb5602a385323dfef337dcbef32323137331045be0c6c9477727e. Estes são os arquivos antigos. Hostinger tem repo bootstrap com modificações locais próprias QA; nunca resetar nem mudar checkout, apenas Git object storage e leitura.

## Objetivo e escopo
Concluir PR #220 e produção da interface reduzida a um único botão “Enviar para o canal no Telegram”. Corrigir no branch PR os manifests QA em apenas quatro atribuições ausentes previamente confirmadas, sem editar qualquer arquivo de anthares-home: recem-grid (A), ler-e-participar-pagina (B). Verificar arquivos e PR HEAD imediatamente antes das mudanças. Rodar lint PHP 8.5, JS, inventário; implantar SOMENTE os 3 arquivos Telegram na Hostinger após backup e SHA check, sem sobrescrever outros arquivos/atores e sem envio real.

## Segurança e recuperação
Preservar todos os dados do fórum, secrets, sessões e dados de venda; rollback íntegro dos três arquivos em erro e manter backup externo privado no próprio servidor. Não instalar serviço novo ou contratar. Compatibilizar plugin com versão atualmente ativa, validar frontend e invalidar cache controlado.

## Status
RUNNING até novo finding append-only com evidências.
