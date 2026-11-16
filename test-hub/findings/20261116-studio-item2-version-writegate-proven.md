# Anthares Studio — Item 2 comprovado: versão ativa e proteção de gravação
STATUS: PROVEN
AREA: anthares-studio-item2-live-version-and-writegate
DATE: 2026-11-16
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43978826585
JOB: 133689677373
COMMIT: 2a98842db152c769e8c1e753a046e8412d9b251e
SUPERSEDES: test-hub/findings/20261116-studio-item2-readonly-lease.md

## Evidências observadas em 16/11/2026 23:23 UTC (19:23 MS)
- PHP e dados lidos diretamente na Hostinger via SSH protegido, sem gravação de opções ou conteúdos.
- WordPress 7.1.4, Anthares Studio plugin 0.7.8-staging.
- Both anthares-studio and original anthares-estudio active.
- Página /studio ID 21383 com post_status=private. Página /estudio original existente.
- anst_writes_enabled=0, anst_trash_cleanup_enabled=0 na instalação real.
- Autorização simulada em memória PHP para usuário permitido ID 106: anst_permission(GET)===true; anst_permission(POST) retorna WP_Error anst_staging_locked, status 423. Não houve requisição POST.
- REST GET anônimo /wp-json/anthares-studio/v1/bootstrap retornou HTTP 401.
- PHP lint PASS, escopo CSS sem page-id-19344 ou post-19344.
- SHA-256 verificados:
  - live new PHP: 042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7
  - live main CSS: 6fc81afb986db6c427da558fd6ed13218575ea90446cbabd0400a9f8e827de97
  - live dark CSS: 2917c1acbfa82098989915b7f1725b729d6345fe920a71398b19f4757563435b
  - original PHP: 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf
- Result signals: STUDIO_ITEM2_SYNTAX=PASS; STUDIO_PHP_LINT=PASS; STUDIO_ACTIVE=1 LEGACY_ACTIVE=1; WRITES_ENABLED=0 TRASH_CLEANUP_ENABLED=0; AUTHORIZED_GET_ALLOWED=1 AUTHORIZED_POST_423=1; ANONYMOUS_REST_STATUS=401; STUDIO_ITEM2_PROVEN=1.

## Consequência
Item 2 concluído. Manter write gate OFF e /studio privado até homologação G4. Item 3: auditoria read-only dos 71 registros e relacionamentos, sem nova migração ou exclusão.
O código live inclui hotfix G4 de restauração e adaptação CSS item 1; não publicar diretamente o PHP base de uma branch isolada sem reconciliação e hash, pois reverteria hotfix.
A execução de auditoria é temporária e não deve ser mesclada como rotina recorrente.
