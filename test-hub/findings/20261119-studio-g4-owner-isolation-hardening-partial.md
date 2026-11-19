# Anthares Studio — endurecimento de isolamento de autores e consistencia da lixeira

STATUS: PARTIAL
AREA: studio/g4/author-isolation
DATE: 2026-11-19
RUN: Anthares Remote jobs 490ab3176194c22dc2fda013bf65f476, ffb7cbf0f73c220519c75a31889ff8e, b76eba685cdeb48e9cb1e44e08232cd2
JOB: UniversoAnthares/anthares-wordpress PR #337
COMMIT: 710cb228683c2bc473a4ba7100692dc0be5f9ba7
SUPERSEDES: none

## Baseline
- G4 prova historica de dois autores no MariaDB isolado, 2026-11-16, Test Hub PR #2636: CRUD por proprietario, negacao 404 ao outro autor, persistencia de Delta, trash/restore em DB isolado. Nao comprova sessao autenticada atual em producao.
- 2026-11-19 codigo PHP do Studio antes do hotfix SHA256 fc393e74c71d513ad39595f13a6b70a3b172f4ebe79e5046b37b866d88890618.
- Original /estudio PHP SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.

## Defeitos corrigidos em producao
1. anst_own() agora devolve apenas posts status publish, do tipo correto e do autor corrente, evitando edicao/leitura escopada de posts na lixeira.
2. anst_purge_project_children($project,$owner): get_posts agora filtra explicitamente autor do projeto e rejeita owner=0; o cron passa post_author do post, mesmo com current_user_id=0.
3. anst_reimport_chapter() exige projeto ativo do autor do capitulo.
4. anst_trash_restore() exige projeto existente, do tipo certo, de mesmo autor e ativo; admite project=0 somente para notas globais.

## Integridade e backups
- Instalado PHP SHA256 7de81057cbd9f637395d0e5c2390925ceac208a466292708381d5f65c28a2e3e; backup privado (modo 600) ~/.anthares-studio-backups/item3-security-20261119T105116Z.php.
- Escrita com hash esperado, lock e substituicao atomica. SHA posterior conferido.
- Original /estudio permaneceu com SHA256 historico intacto.
- Nenhuma tabela, identidade, permissao ou dado de escritor alterado.

## Provas executadas
- PHP lint PASS; 37/37 Python regressions do plugin instalado PASS.
- 41 asserts PHP com funcoes reais extraidas do plugin e mocks em memoria PASS: status/proprietario, filtragem do cascade por autor, prevencao de restore orfao/outro autor, restore valido.
- Endpoint anonimo https://anthares.us/wp-json/anthares-studio/v1/bootstrap HTTP 401; pagina /studio/ HTTP 200.
- Branch de codigo PR #337: tres testes adicionais regressivos em test_isolation.py. 93 testes totais com 6 falhas, **as mesmas 6 falhas preexistentes** na branch-base PR #336 (90 testes com seis falhas em navegacao G6/CSS). Logo os novos testes de isolamento passaram; nao registrar 93/93.
- Preflight manifesto QA 705/705 exactly-once PASS; PHP lint e Bun browser build PASS na branch.
- Artefatos QA efemeros removidos.

## Limites e proxima acao
A instalacao de identidades de teste e as escritas REST autenticadas foram explicitamente recusadas pela ferramenta em rodada anterior. Respeitar a negativa: nenhuma rota secundaria para realizar essas operacoes. A conclusao real do item 3 requer duas contas autenticadas e autorizadas, verificacao E2E das operacoes CRUD, rejeicoes cruzadas, refresh readback, restore e autorizacao em browser mobile/desktop. Portanto resultado do item 3 segue PARTIAL, com correcao de codigo em producao e sem atestar autorizacao real multifuncional.

Cuidado: o PR #337 depende de #336; merge/deploy dessa arvore exige reconciliacao com o runtime vivo e com as seis falhas preexistentes de G6/CSS.
