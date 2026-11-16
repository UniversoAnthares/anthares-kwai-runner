# Anthares Studio — G5 esquema ACF offline validado; lease encerrado
STATUS: PARTIAL
AREA: studio-acf-schema-design
DATE: 2026-11-16
JOB: acf-core-fields-schema-20261116
OWNER: ChatGPT — CURSO ESCRITA CRIATIVA
SOURCE_REPO: UniversoAnthares/anthares-wordpress
SOURCE_BRANCH: feat/studio-g3-migration-dryrun-20261116
SOURCE_SHA: ee480a823674318a5c55c07444505a4646930713
RESULT_BRANCH: feat/studio-g5-acf-schema-contract-20261116
RESULT_SHA: 1d812fbd5ba45f4da364c22ef50d0e98a5802022
RESULT_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/308
LEASE_SUPERSEDED: test-hub/findings/20261116-1713-lease-studio-acf-schema-prep.md
LEASE_STATUS: RELEASED

## Evidências verificadas
- Foram criados 12 grupos ACF Local JSON com 39 campos e 51 associações explícitas aos metadados de origem; branch/PR DRAFT, sem merge e sem runtime loader.
- Todos os grupos estão com active=false e show_in_rest=0. ACF Free 6.8.11 está ativo no WordPress, ACF Pro 5.10.2 está inativo; foram utilizados tipos gratuitos.
- Chaves ACF exclusivas studio_*, mantendo _studio_* reservadas às referências ACF, para evitar sobrescrever os dados originais contidos em _anst_delta e _anst_project.
- Incluídos os campos históricos JSON, Delta, recuperação e proveniência, 4 CPTs, opções de curso planejadas e agregação de zoom por usuário.
- Testes no Hostinger em clone temporário da branch de desenvolvimento: python unittest 22/22 PASS, qa/manifest-coverage-preflight.py auditable=654 assigned=654 exactly_once=yes, orquestrador PHP 11 contratos PASS. Diff deste commit: 15 arquivos novos e 2 manifestos QA sincronizados, sem alteração PHP/JS/CSS/Quill.
- Conferência em produção após commit: SHA original anthares-estudio.php 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf; plugin antigo 0.7.7 e clone 0.7.8-staging ativos; dados 40 publish + 31 trash em cada namespace; anst_writes_enabled=0 e anst_trash_cleanup_enabled=0. Diretório acf-json do clone instalado: zero arquivos novos (nenhum deploy).
- Reconciliada diferença da configuração de aulas: fonte bruta NULL/ausente, cópia contém array vazio; com fallback da aplicação ambos equivalem à lista vazia, sem conteúdo de aula perdido nessa opção.
- Perfis AntharesWordPressAdmin e AntharesHarness testados em Chrome invisível; ambos sem acesso autorizado à página privada /studio (404), e sessões lançadas foram encerradas. G4 capturas visuais permanecem bloqueadas até sessão autenticada comprovada.

## FAILED_AVOIDED
- Nunca apontar ACF para chaves de armazenamento antigo _anst_*; não executar update_field em produção nesta etapa.
- Nenhuma alteração ao plugin original, banco, opções, visibilidade da página ou fluxo de edição.
- Nenhum bypass de autenticação da página privada; nenhuma sessão Chrome persistente própria.
- Respeitado ownership: somente arquivos ACF JSON e documentação/testes novos, mais manifestos QA.

## Gates posteriores
- G1/G4: falta baseline visual autenticado completo e teste de regressão de escrita/restauração em /studio.
- G5: schema inicial 12 grupos pronto, adapter load_json, migração ACF e alterações de repositório ainda pendentes; grupos ANST09-12/15 para novas entidades ficam condicionados aos CPTs.
- PR de segurança cron #307 permanece draft e sem deploy. Outros agentes atualizaram G3; reconciliar novos commits antes de merge.

## Resultado
STATUS_FINAL: PARTIAL_SCHEMA_READY_OFFLINE; DEPLOY=NO; DATA_WRITE=NO.
Proxima execução requer lease novo, revisão da PR #308 e aprovação visual G4 antes de ativar qualquer campo ACF.
