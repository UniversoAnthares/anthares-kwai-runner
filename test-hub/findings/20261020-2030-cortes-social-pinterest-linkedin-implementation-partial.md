# CORTES Pinterest/LinkedIn — código e CI, ativação ainda pendente
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-20
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39521426965
JOB: GitHub Actions read-only-contract / 39521426965
COMMIT: f9b2fc7f3cc3677dc26f075468bdc7027fa9c21b
SUPERSEDES: test-hub/findings/20261020-2005-lease-cortes-pinterest-linkedin-editorial.md

## Objetivo
Aplicar o sufixo editorial obrigatório, site nas legendas e tags, remover o teto fixo Pinterest, preservar LinkedIn 20/dia e criar base real de publicadores integrados à fila.

## Resultado
PR #269 DRAFT contém editoriais idempotentes, adaptadores oficiais Pinterest/LinkedIn, consumidor por lease/fence/confirm, guarda transacional LinkedIn 20/dia no servidor Neon e ausência de quota fixa Pinterest. Scripts de Kwai físico, TikTok cloud, Instagram e adaptador Instagram/Threads/X receberam atualização. PR normativo do Clipper #102 também permanece DRAFT. Nenhum deploy/live publish desta integração ocorreu.

## Evidência decisiva
GitHub Actions run 39521426965 SUCCESS: syntax Python, 11 testes da nova suíte, 8 do modelo, contrato antigo de social adapters, patch Cloudflare em snapshot descartável e Node syntax da fila Neon. Run 39521426992 SUCCESS: Anthares Publisher QA. Anthares Remote SYSTEM executou separadamente CORTES_SOCIAL_ALL_QA_PASS. Banco Neon project purple-flower-35918989, tabela cortes_publications, possui jobs de Kwai e zero jobs Pinterest/LinkedIn no momento da consulta. Não foi modificado.

## Pendências operacionais
1. Configurar OAuth/permissões e tokens, board/capa Pinterest e author URN LinkedIn no secret store do executor. Variáveis locais não estavam definidas; inventário de GitHub secrets inconclusivo por CLI sem autenticação.
2. Habilitar producer/despacho dos masters curtos para target_keys específicos. Consumidor criado, sem orquestração/agenda live ainda.
3. Integrar em main/deploy após revisão, sem atropelar ruleset; comprovar uma publicação real por plataforma, com URL/ID e confirmação no ledger.
4. Migrar títulos/descrições dos publicadores externos WordPress/YouTube/Facebook para garantir universalidade integral. Estilos em código deste PR são cobertura parcial, devidamente declarada.
5. Preservar filas existentes/UNCERTAIN, especialmente Kwai e TikTok. Nada foi resetado.

## Consequência
Nunca afirmar Pinterest/LinkedIn ACTIVE ou regra universal em produção com base apenas no CI. Continuação deve obter autorização externa, auditar identidade/quota e cumprir o fluxo do Test Hub antes de ativar qualquer job real.
