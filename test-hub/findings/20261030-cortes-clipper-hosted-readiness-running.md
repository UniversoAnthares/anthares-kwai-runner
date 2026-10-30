# CORTES Clipper — readiness do executor externo (30/10/2026)
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-30
RUN: pending first main push of isolated workflow
JOB: none
COMMIT: pending
SUPERSEDES: none

## Objetivo
Verificar no executor público GitHub-hosted, de forma somente leitura, a possibilidade técnica de executar a fonte privada CORTES com as dependências de `cortes-daily.yml` e `cortes-short-resume.yml`, mantendo as publicações atuais.

## BASELINE_PROVEN
- Os dois workflows de produção privados exigem runner self-hosted Windows.
- O runner mantém logs e workspaces em C:, com atividade atual.
- O plano de quota vigente registra GitHub Actions privado como BLOCKED_QUOTA e GitHub Actions público como disponível.
- A cadeia já possui clonagem privada de somente leitura no workflow público `private-ci-quota-rescue.yml`.

## FAILED_AVOIDED
- Alterar `runs-on` dos produtores antes da prova de quota, segredos, checkpoints remotos e publicação reconciliada.
- Duplicar publicações ou usar D: como novo armazenamento persistente.
- Enviar arquivos de mídia, ledgers privados ou credenciais como artifacts públicos.

## SUCCESS_SIGNAL
`CORTES_HOSTED_READONLY_GATE=PASS` em GitHub-hosted `ubuntu-24.04`, com clone privado autorizado, compilação dos dois componentes e preflight de mídia com scratch efêmero.

## FAILURE_SIGNAL
`CLIPPER_SOURCE_READ_DENIED`, `CLIPPER_SOURCE_READ_CREDENTIAL_NOT_AVAILABLE`, `CORTES_HOSTED_PYTHON_DEPENDENCIES_FAILED`, ou `CORTES_HOSTED_MEDIA_PREFLIGHT_FAILED`.

## TEST_VALIDITY
Válido somente se o job for alocado em `ubuntu-24.04` do GitHub e clonar a origem privada de forma autenticada. Resultado positivo prova apenas a camada de execução/compatibilidade. Migração dos produtores depende de ledger durável externo, autorização do WordPress e fila Neon, quotas independentes e handoff com exclusão mútua. Nenhum vídeo é publicado ou descartado nesta prova.

## Alteração
Novo workflow público de prova isolada, acionado uma vez por push do próprio arquivo no main e manualmente. Nenhuma agenda ou publicador alterado.
