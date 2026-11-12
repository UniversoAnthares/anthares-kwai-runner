# CORTES — três adaptadores sociais em PRs independentes
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-23
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/185
JOB: Anthares Remote (Windows/Python 3.12), QA temporário
COMMIT: 1b66f29bde563b294b64b03d3b7f99e31e632952
SUPERSEDES: test-hub/findings/20261023-cortes-release-candidate-and-72-regressions-partial.md

## Objetivo
Iniciar migração de Instagram, Threads e X preservando rigorosa exclusividade
de diretórios por rede. Não modificar workflow social legado.

## Resultado
PRs em draft, cada qual com quatro arquivos:
- #186 Threads: https://github.com/UniversoAnthares/anthares-clipper/pull/186
- #187 Instagram: https://github.com/UniversoAnthares/anthares-clipper/pull/187
- #188 X: https://github.com/UniversoAnthares/anthares-clipper/pull/188
Cada PR contém somente networks/<rede>/adapter.py,
networks/<rede>/ownership.json, docs/networks/<rede>/README.md e
tests/networks/<rede>/test_adapter.py. Não altera outro publicador.
Os adapters aceitam transporte/credenciais explícitas e legenda aprovada
com SHA de transcrição. Nenhum executor, fila, browser, token ou deploy foi
modificado. A etapa não publica nem valida legenda contra transcrição real.

## Evidência decisiva
Windows/Python 3.12: Threads 10 PASS, Instagram 10 PASS, X 12 PASS.
Novo guard estático de manifestos na PR #185: 12 PASS.
Guard de escopo de paths na PR #185: 16 PASS após endurecimento que
impede branches plataforma/ de misturarem caminhos não relacionados.
Validação conjunta dos manifestos e adapters reais (composição apenas
em staging): status PASS, deploy_authorized false,
credenciais declaradas Threads=1, Instagram=2, X=4.
GitHub PR changed files confirmado: exatamente quatro caminhos por rede.
Scope evaluation: approved-paths:threads/instagram/x, cada qual isolada.

## Consequência
STATUS PARTIAL. Quatro PRs draft (#185-#188) e findings #1258.
Não estão separadas identidades de OS/ACL Windows, segredos reais,
fila, ledger, dispatcher, cloud runners ou rollback independente.
Não integrar as PRs dos novos publicadores antes de ativar controle de
escopo em CI e desenvolver transporte com contas/token próprios.
Testes foram offline; nenhuma prova de publicação de destino.
