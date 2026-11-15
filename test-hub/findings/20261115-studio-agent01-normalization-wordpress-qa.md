# Anthares Studio — Agente 01: normalização homologada em WordPress real
STATUS: PARTIAL
AREA: architecture
DATE: 2026-11-15
RUN: WordPress Hostinger 7.1.4 / PHP 8.3.36; staging isolado
JOB: Anthares Remote 6647029e026d3dfd2ef329ee06ca3ce9
COMMIT: UniversoAnthares/anthares-wordpress fb2b4da384943307388da179103a9175bff4c082
SUPERSEDES: none

## Objetivo
Validar a normalização idempotente de JSON ACF, preservação de IDs e documentos Delta, isolamento e recuperação, sem alterar o estúdio antigo.

## Resultado
Execução WP-CLI com plugin carregado de staging isolado (plugin ativo omitido exclusivamente do processo CLI). `NORMALIZATION_INTEGRATION=PASS`, `QA_FIXTURES_CLEANED=5`. PASS: EMPTY_PROJECT, LEGACY_UNLOCK_V1_VALIDATION, LEGACY_READ_BEFORE_CONVERSION, BACKUP_ATTESTATION_FAIL_CLOSED, SIMPLE_CONVERSION_AND_IDEMPOTENCE, COMPLEX_ELEMENTS_REVIEWS_VERSIONS_AND_LINKS, QUILL_DELTA_AND_LEGACY_JSON_BYTE_PRESERVED, REST_AUTHORIZATION_AND_CANONICAL_REFERENCES, CONFLICTED_CANONICAL_ID_READABLE, STALE_SOURCE_CONFLICT_BLOCKED, INVALID_REFERENCE_BLOCKED.

`php -l`, teste estático de privacidade/ACF e contrato ACF: PASS; 12 grupos ACF e 61 campos da base testada. Integridade dos arquivos de staging comparada pelos hashes blob Git.

Inventário real somente leitura do novo Studio: `projects=0`, `candidates=0`, `issues=0`, `conflicts=0`. O estúdio antigo mantém inventário anterior de 40 publicados e 31 na lixeira, gerido por importador separado.

## Consequência
PR canônica de normalização: UniversoAnthares/anthares-wordpress#285. PR #283 encerrada sem merge, histórico preservado. Escrita falha fechada sem verificação independente de backup recuperável por `anst_normalization_backup_verified`. Pendem importação real do Agente 04, reconciliação com entidades ACF tipadas e cutover dos consumidores de Planejamento, Manuscrito, Revisão e Análises. Não afirmar homologação ponta a ponta nem migrar dados reais antes dessas provas.
