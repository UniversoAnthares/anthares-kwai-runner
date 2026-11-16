# Anthares Studio — integração ACF: runtime G5 homologado, extensão de aulas pendente
STATUS: PARTIAL
AREA: studio-g5-acf-runtime-preparation
DATE: 2026-11-16
OWNER: ChatGPT — CURSO ESCRITA CRIATIVA
JOB: studio-g5-runtime-adapter-20261116
SOURCE_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/311
G5_BASE_SHA: bba7660d2705bb87d7db9605eaf408cbcc9e176d
LAST_FULL_RUNTIME_QA_SHA: 2bce545faa6039c56aef874ae6166deff6037f4c
CURRENT_DEVELOPMENT_SHA: 3fb80a53e087ef8d0bc9d8f88ffa46a0f3d3dae6
LIVE_PLUGIN_SHA256: 477f4e2dd2fe1cc79c0f0793109c257edb212d0e16e68f68c3278d323233a7b3
LEGACY_PLUGIN_SHA256: 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf
SOURCE_LEASE: test-hub/findings/20261116-studio-g5-runtime-adapter-lease.md
LEASE_STATE: RELEASED
NOT_PUBLISHED: G5 ACF runtime code not present in live plugin.

## G5 backend ACF ON/OFF — verificado no banco isolado
- Snapshot do WP de 16/11, checksum validado, restaurado em MariaDB privado com `--skip-networking` e socket UNIX, eliminado ao final.
- Migrador transacional baseline: 412 campos postmeta + 1 ficha de zoom do usuário; primeira passagem `written=413 skipped=0`, segunda `written=0 skipped=413`; 71 ANST e 71 AEST no início.
- Modo ACF OFF: REST de origem e clone com mesmo volume para dois proprietários; metadados e 7 Deltas históricos idênticos, POST 423.
- Modo ACF ON: dois proprietários com projetos 15/15 e 2/2, notas 12/12 e 0/0, capítulos 4/4 e 2/2, cartões 5/5 e 0/0.
- As 7 versões Quill antigas estão idênticas byte a byte quando lidas pelo ACF, e as 5 preferências antigas de zoom foram verificadas. Novo zoom gravado exclusivamente em ACF.
- CRUD REST de projeto, nota, cartão e capítulo; Quill JSON com acentos, backslash, Unicode e bold preservado; campos novos persistidos em studio_*; relações consultadas por campo ACF.
- Tentativa de atualização por outro proprietário 404; lixeira/restauração e WRITE_LOCK 423 aprovados. Registros finais da base isolada: 71 AEST e 75 ANST (4 artificiais), limpeza concluída ao encerrar.
- Testes Python 39 PASS e QA 662/662; 5 CSS/JS assets auditados na produção: 4 idênticos byte a byte (ambos CSS, Quill JS e Quill CSS); JavaScript customizado difere apenas nos identificadores de rota, estado scroll, tema com fallback e tipos na lixeira, conforme diff verificado. Essa prova estática NÃO substitui QA visual autenticado.

## Extensão de vídeos das aulas — NOVO CÓDIGO, AINDA SEM TESTE DINÂMICO
- Commit atual 3fb80a53 acrescenta campo ACF de opções editoriais `studio_course_lesson_links_json` via `post_id='option'`, preservando `anst_section_lesson_videos` para rollback.
- A opção editorial entra no fingerprint e nos controles transacionais do migrador. Contagem esperada passa a 414 (412 postmeta + 1 zoom + 1 opção de aulas). ACF Free fornece métodos get_field/update_field; a UI de Options Pages é PRO, portanto não foi habilitada.
- PHP lint do plugin, adaptador, migrador e fixture: PASS. Testes Python 40 PASS, QA 662/662 PASS (19:05 UTC).
- Integração da opção ACF com 414 valores **AINDA NÃO HOMOLOGADA**: conectores remotos retornaram `control 500 internal_error`; nenhuma evidência de execução v4 válida. A PR #311 permanece DRAFT; fluxo antigo de vídeos em produção continua intacto.
- A configuração legada de vídeos observada no snapshot é lista vazia; a ausência de vídeos no legado permite teste sem divulgar URLs privadas.

## Próximos gates
1. Reexecutar `anthares-studio/tests/integration/g5-runtime-isolated.sh` para SHA atual numa nova sessão Hostinger estável. Provar migrador 414/414, roundtrip ACF de opções e resto do CRUD.
2. Revisar G4 visual: Chrome autorizado, desktop/mobile, navegação; browser WordPressAdmin e Harness atuais não possuem sessão capaz de abrir página privada /studio, sem elevar privilégio.
3. Reconciliar PRs #307, #308, #309, #310 e #311 na branch de integração antes de qualquer merge ou deploy G5. Verificar opções editoriais e mapeamento de 39 campos, classes CSS/JS, segurança.
4. Preservar /estudio, /studio privado e flags `anst_writes_enabled=0`, `anst_trash_cleanup_enabled=0`, `anst_acf_runtime_enabled=0` (ausente em live); migrador `--apply` proibido em produção até G4 e aprovação formal.
5. G6 navegação, G7 requisitos narrativos 001–188, G8 homologação completa continuam pendentes.

## Proibição de extrapolação
Os testes PASS de backend anteriores ao commit de opções não validam a nova transferência editorial. A correção G4 de restauração está ativa na produção; ACF runtime está exclusivamente em branch. Não classificar o projeto inteiro como concluído.
