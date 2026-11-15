# Anthares Studio: normalização do item 4 — QA WordPress real

STATUS: PARTIAL
AREA: architecture
DATE: 2026-11-15
RUN: Anthares Remote/ARA SSH, WordPress real da Hostinger, código isolado
JOB: ARA edc7cdfe6e49150f2bfb240e4d175882
COMMIT: UniversoAnthares/anthares-wordpress f8d814c3aca8ffac8e5375e6be56c2531612b99f
SUPERSEDES: none

## BASELINE_PROVEN

Implementação do item 4 e correções de versão por capítulo, reconciliação de edição da origem, projeções órfãs e isolamento de autores integradas na branch `feat/anthares-studio-acf-20261114`. ACF de 313 campos integrado. A suíte usou checkout isolado do código, `--skip-plugins=anthares-studio`, PHP 8.3.36 e banco WordPress real, criando somente registros sintéticos.

## SUCCESS_SIGNAL / TEST_VALIDITY

Exit 0 e `QA_FIXTURES_CLEANED=13`. Vinte e três PASS: EMPTY_PROJECT; LEGACY_UNLOCK_V1_VALIDATION; LEGACY_READ_BEFORE_CONVERSION; BACKUP_ATTESTATION_FAIL_CLOSED; SIMPLE_CONVERSION_AND_IDEMPOTENCE; COMPLEX_ELEMENTS_REVIEWS_VERSIONS_AND_LINKS; QUILL_DELTA_AND_LEGACY_JSON_BYTE_PRESERVED; FOUR_AREAS_SAME_RECORD_ID; NATIVE_ACF_LIVE_UPDATE_IN_FOUR_AREAS; UNIFIED_OWNER_ISOLATION; READTHROUGH_BEFORE_MATERIALIZATION; EXPLICIT_SEMANTIC_KIND_WITH_FREE_FOLDER_FALLBACK; FOLDER_RECLASSIFICATION_BLOCKS_DUPLICATION; TYPED_PROVENANCE_NO_DUPLICATE_AND_LIVE_EDIT; UNIFIED_REST_ROUTE; REST_AUTHORIZATION_AND_CANONICAL_REFERENCES; CONFLICTED_CANONICAL_ID_READABLE; SOURCE_EDITS_SHARED_WITH_CONFLICT_FLAG; REST_LIVE_SOURCE_WITH_STABLE_ID; STALE_SOURCE_CONFLICT_BLOCKED; ORPHANED_PROJECTION_PRESERVED_AND_BLOCKED; CHAPTER_SCOPED_VERSION_IDENTITIES; INVALID_REFERENCE_BLOCKED.

PHP lint: seis arquivos do normalizador, bootstrap e entities.php, oito PASS. `php qa/anthares-orchestrator-qa.php`: onze PASS, cobertura 100% e manifestos idênticos; job ARA 95cf9e22b0a1f352e0c79d94292855c3. Os hashes de blob dos seis arquivos normalizadores e do adaptador de entidades publicados no site coincidem com o HEAD de integração; bootstrap difere apenas no comentário de inclusão. Checkouts temporários removidos: CLEAN_A e CLEAN_B.

## FAILED_AVOIDED / FAILURE_SIGNAL

Toda escrita exige SHA de origem, confirmação de projeto e filtro que comprove backup restaurável. Sem verificador de backup, falha fechada. Duplicatas, referências órfãs e divergência de versões bloqueiam reaplicação. Testes criaram registros próprios e eliminaram treze fixtures no `finally`. Nenhum projeto legado, Quill Delta ou documento JSON de usuário foi modificado.

## Estado real e dependência remanescente

WP-CLI encontrou 17 projetos publicados em `aest_projeto` e zero projetos publicados em `anst_projeto`. A importação dos 40 registros legados permanece sob responsabilidade do Agente 04/PR #286. A integração do grafo de relações PR #282 e a adoção integral pelas telas continuam independentes. Os testes comprovam o módulo em WordPress real com dados sintéticos; transferência de usuários reais, backup restaurado e liberação geral do estúdio ainda requerem validação.
