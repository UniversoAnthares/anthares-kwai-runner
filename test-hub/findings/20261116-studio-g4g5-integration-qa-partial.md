# Anthares Studio G4/G5/G6 — integração preparada e testada, homologação visual pendente
STATUS: PARTIAL
AREA: studio-g4-visual-and-g5-acf-navigation-integration
DATE: 2026-11-16 (America/Campo_Grande), execuções 2026-11-17 UTC
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
SUPERSEDES: test-hub/findings/20261116-studio-g4g5-integration-lease.md
SOURCE_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/314 (DRAFT)
SOURCE_BRANCH: integration/studio-g4-g5-g6-20261116
PRODUCTION_DEPLOY: NO

## G5+G6 com banco isolado: PROVEN
- Run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44007136078 / job 133785085805: branch G6 head 3efad7ad3b41e765132f625202daad88f8f2ee7d; 47 unit tests, manifest 665/665, PHP lint, G5 MariaDB snapshot, dry-run, primeira e segunda aplicação ACF, OFF/ON e REST fixture, 71 posts / 7 Quill / 2 autores, cleanup.
- Run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44008570966 / job 133789765058: versão integrada com quatro arquivos literalmente iguais aos Git blobs da PR314; sinais INTEGRATION_SOURCE_MATCH=4_OF_4_GITHUB_BLOBS, INTEGRATED_UNIT_TESTS_PASS=48, INTEGRATED_PHP_LINT=PASS, INTEGRATED_MANIFEST=PASS, INTEGRATED_G5_RUNTIME_PASS=1, INTEGRATED_QA_PRIVATE_CLEANUP=1.
- A PR314 reconcilia CSS 509+216 seletores novos e seis artigos, body class exclusiva, cron trash guard e wp_untrash status, com ACF Free, migração 414 campos e cinco entradas globais/sete grupos internos. Quill vendor permanece intacto. PR permanece em draft sem merge.

## G4 visual: BLOCKED / NOT_PROVEN
- Backend G4 em ensaio de base isolada anterior: projetos, notas, capítulos, cartões, Quill, lixeira, owner/REST/423.
- Execuções de screenshots desktop/mobile usando usuário administrador sintético em WordPress restaurado: runs 44008858506, 44008967722, 44009319099, 44009649461, 44009924522, 44010192239. Nenhuma obteve a matriz de capturas.
- Evidência causal: G5_RUNTIME_INIT_DB e G5_RUNTIME_RESTORE_DB, processo PHP local aparentemente vivo, porém curl localhost 127.0.0.1 retornou código de conexão 7 (HTTP 000), inclusive sem proxy. PHP -S em loopback na Hostinger indisponível para esse ambiente. Nenhuma conta real/cookie real foi utilizada. Nenhuma escrita em produção.
- G4 exige screenshots autênticas antigo/novo desktop/mobile, claro/escuro, estados 0/1/N projetos e matriz C001-C025. PHP lint e testes unitários não substituem esse aceite.
- Não repetir a rota PHP -S idêntica sem nova mudança causal comprovada; preferir perfil de navegador autorizado ou ambiente isolado com HTTP efetivamente disponível.

## Produção observada
- HTTP em 2026-11-17 03:28 UTC: CSS principal tem 509 ocorrências anst-studio-page e zero page-id-19344. Novo asset G6 studio-g6-navigation.css responde 404, portanto navegação preparada ainda não está publicada.
- Estado anterior da base: 71 AEST / 71 ANST, 7 Deltas, zero divergências. Write/cleanup flags OFF em auditoria anterior. Original preservado.
- G5 runtime não foi implantado nesta execução. A PR314 não foi mesclada.
- Nenhuma sessão pessoal reutilizada, nenhum plugin original alterado, backup intacto.

## Consequência
- Item 4: PARTIAL (backend comprovado, QA visual pendente).
- Item 5: PARTIAL (ACF/G6 código e isolamento comprovados, deploy/homologação live pendentes).
- Próxima publicação exige screenshots G4 e matriz C001-C025, backup, hash, migração ACF transacional e front G6 validado. Nenhuma flag live pode ser habilitada apenas para declarar o trabalho concluído.
