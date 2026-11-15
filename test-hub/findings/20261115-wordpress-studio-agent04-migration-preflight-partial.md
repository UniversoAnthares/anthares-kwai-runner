# Anthares Studio / Agente 04 — migração legada
STATUS: PARTIAL
AREA: github
DATE: 2026-11-15
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/286
JOB: Hostinger PHP 8.3.36, WP-CLI dry-run e verify; fixtures isoladas
COMMIT: 1b57cd292d19a204e2335d6aa49a6740640e1269
SUPERSEDES: none

## Objetivo
Implementar importador idempotente aest_* para anst_* com modo dry-run padrão, ACF, proveniência e recuperação segura.

## Resultado
- PR #286 draft para a branch de integração #275. Sem alterações na versão antiga.
- Testes de sintaxe em PHP 8.3.36 e fixture: PASS. Incluem Quill Delta,
  links, autoria, lixeira, checksums, bloqueio de backup adulterado,
  alteração concorrente da origem, rollback com drift e retomada interrompida.
- WordPress real, dry-run: completed=true; eligible=40 (17 projetos,
  8 ideias, 4 notas, 5 cartões, 6 capítulos); trash_preserved=31;
  errors=0; divergences=0; recoverable=40.
- WordPress real, verify: completed=false (40 alvos pendentes);
  errors=0; divergences=0; recoverable=40.
- Checksum do plano: `4607b131043191ac2a6d74992cd76891201e84f07827fcdd674b06a59a73b236`.
- Nenhum test-copy ou execute de dados reais efetuado.

## Evidência decisiva
`MIGRATION_FIXTURE=PASS cases=source-preservation,trash,ACF,Quill,backup-tamper,authorization,checksum,idempotence,relations,source-drift,target-drift,rollback,resume`.
`QA_MANIFEST_PREFLIGHT=FAIL`: cinco arquivos novos exigem cadastro nos manifestos globais.
PRs #282, #284 e #285 pendentes de integração; uploads reais somam cerca de 15 GB.
Backup integral recente com restauração verificável não foi localizado nas pastas privadas examinadas.

## Consequência
Manter importação definitiva bloqueada até integração de ACF,
normalização e relacionamentos, QA preflight aprovado,
backup restaurável, test-copy dos 40 materiais e autorização explícita.
Preservar os 31 itens na lixeira. Nenhum campo aest_* foi modificado.
