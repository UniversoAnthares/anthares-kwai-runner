# Studio G6 — sete grupos fixos implantados

STATUS: PARTIAL
AREA: studio/g6/navigation
DATE: 2026-11-19
RUN: Anthares Remote 3367269c2d634406aaf9de2dcd6ed542
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/340
COMMIT: b9a4a54cd9dad1f8b0bac1be9cd51d0c99ac7d5f
SUPERSEDES: none

## Escopo
Contrato aprovado em 13/11/2026: sete areas internas de projeto. O Studio tinha nove abas por compatibilidade com o legado. A versao nova agora apresenta Visao geral, Pesquisa, Planejamento, Manuscrito, Analises, Revisao e Publicacao. Elementos e Estrutura foram convertidos em subtelas de Planejamento, preservando rotas e handlers. Breadcrumb identifica projeto/grupo e oferece retorno a Meus projetos e Trocar projeto. Menu global de cinco entradas preservado.

## Evidencias
- SHA256 do JavaScript instalado: adbe9a4e9c6600054c00a06320930c0be743aea23ce99ac50cdc573308a8ec73.
- Backup privado Hostinger: /home/u566597497/.anthares-studio-backups/seven-nav-prev-20261119T151624Z.js (modo 0600).
- SHA256 PHP legado /estudio/: 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf, intacto.
- Build JS Bun PASS, QA manifest exactly once 705/705 PASS.
- 37 testes do plugin instalado PASS.
- Suíte expandida na branch GitHub: 93 testes, 3 falhas preexistentes em compatibilidade de ações legadas, importacao Quill e CSS historico; antes desta alteracao havia 6 falhas.
- Comparacao estâtica das acoes do Studio vs legado confirmou 59 handlers compartilhados e 16 tipos de formularios legados presentes, sem comprovar paridade de comportamento.

## Limites e continuidade
Os testes manuais de duas contas e cliques reais foram explicitamente adiados pelo titular ate o Studio estar terminado. Nao os solicitar de novo nesta etapa. As 188 funcionalidades permanecem sujeitas a verificacao por fase. Preservar alteracoes exclusivas no JavaScript da Hostinger (retencao de lixeira e ajustes de codigo) ao consolidar a PR: nao fazer deploy cego de toda a arvore GitHub. PR #340 e rascunho, dependente de #338.
