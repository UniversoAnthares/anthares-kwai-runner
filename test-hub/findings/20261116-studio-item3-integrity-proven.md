# Anthares Studio — Item 3 concluído: 71 pares íntegros em produção
STATUS: PROVEN
AREA: studio-g3-71-records-readonly-integrity
DATE: 2026-11-16 (local America/Campo_Grande), execução UTC 2026-11-17T02:30
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44003428665
JOB: 133772856128
COMMIT: 675401c488715ddffed2dd84523f3ddc0b417f9f
SUPERSEDES: test-hub/findings/20261116-studio-item3-integrity-lease.md
PREVIOUS_BASELINE: test-hub/findings/20261116-studio-g3-integrity-rest-readonly-verified.md

## Evidência do WordPress ativo, somente leitura
- SOURCE_COUNT=71; TARGET_COUNT=71; MAPPED=71; zero entradas adicionais ou proveniência duplicada.
- Post types idênticos de origem/destino, com prefixos respectivos AEST/ANST: 35 projeto, 13 nota, 7 capítulo, 16 cartão. Inclui registros de lixeira.
- STATUS_publish=40 e STATUS_trash=31, em ambas as instalações.
- SOURCE_CHECKSUM_MATCH=71; SOURCE_FINGERPRINT=efbe0aea9f69979ec0122239329d7471c6370092718f845f3bd3a8a4833fea8c; reconsulta da fonte estável.
- FIELDS_MATCH=71 e POST_META_MATCH=71; verificados tipo, status, autor, título e conteúdo, datas, slug, ordem, parentalidade, excerpt, outros campos preservados no importador; metadados brutos comparados com remapeamento dos IDs.
- DELTA_COUNT=7; DELTA_RAW_MATCH=7; DELTA_VALID=7. Documentos Quill com JSON válido e conteúdo bruto equivalente, sem qualquer exposição dos textos.
- PROJECT_REFERENCE_COUNT=36 e ORPHAN_REFERENCES=0. Vínculos remapeados com IDs exclusivos, autor conferido contra projeto.
- GLOBAL_IDEA_COUNT=8: notas sem projeto, referenciadas por valor zero, comportamento explicitamente permitido por anst_create_note() no código do plugin. O primeiro teste classificava incorretamente essas notas; a regra do auditor foi ajustada e reexecutada.
- USER_ZOOM_SOURCE=5; USER_ZOOM_TARGET=5; correspondência exata.
- ISSUES=[]; anst_writes_enabled=0; anst_trash_cleanup_enabled=0.
- Plugin original SHA256=13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf; clone live SHA256=042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7; checks antes e depois.
- SUCCESS_SIGNAL: STUDIO_ITEM3_INTEGRITY_PROVEN=1.
- Arquivos do WordPress, posts, usermeta, options, REST e ambiente não sofreram mutações nesta auditoria.

## Diferenciação dos testes
- Validação da idempotência observável: os 71 documentos originais têm uma única cópia com origem/checksum correspondente; cenário de reimportação idêntica requer 0 inserções.
- Ensaio de segundo --apply em MariaDB isolado não foi realizado nesta execução e pertence à homologação da migração G3 completa, fora do escopo limitado do item 3 (auditar integridade dos dados já importados).
- Interface visual autenticada e testes CRUD isolados continuam sendo o item 4 / G4.
- Permanecem /studio private, gravação e limpeza da lixeira OFF, /estudio preservado.
