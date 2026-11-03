# Lease — suspensão em produção dos CRON CORTES dependentes de runner pessoal
STATUS: RUNNING
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/230
JOB: none
COMMIT: 39e2eee3366e713a3488b4f5086fff3eed3761f5
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / REMOTE-ADMIN
LEASE_START_UTC: 2026-11-03T20:31:48.031Z
LEASE_EXPIRES_UTC: 2026-11-03T20:56:48.031Z
GOVERNANCE_MANIFEST: 223433740e807a90
TARGET_REPO: UniversoAnthares/anthares-clipper
TARGET_BASE_SHA: 9ee0b7c2501c4bf223bbed4203c8a06f3fe9ca46
TARGET_PR_HEAD_SHA: 39e2eee3366e713a3488b4f5086fff3eed3761f5
SCOPE: merge aprovado pelo titular de PR #230, remoção de on.schedule dos dois workflows self-hosted Windows, preservando workflow_dispatch e demais etapas.

## BASELINE_PROVEN
- Decisão expressa do titular em 2026-11-03: concluir a suspensão de agendamentos dependentes de PC, custo R$0, sem arquivos de trabalho no PC.
- Único runner GitHub do Clipper: DESKTOP-FTDK0HP offline; Anthares Remote encontrou zero processos de runner e zero tarefas de runner habilitadas.
- PR #230 é draft, patch de somente quatro linhas removidas (blocos schedule), zero adições; arquivos/SHAs conferidos contra o main. Últimos runs desses workflows são falhas de 2026-10-30. Não há produção comprovada via PC atualmente.
- Preservação: workflow_dispatch e código de publicação/ledger intactos; nenhum vídeo, job ou fila será publicado.
- O espelho GitLab Clipper está desatualizado e não contém esses dois arquivos: sem sincronização cega.
- Baseline hosted read-only PROVEN, run 41116819377 (FFmpeg/compilação). Não comprova publicação remota nem cutover.

## FAILED_AVOIDED
- Manter cron */5 para ativar o PC ou rodar com quota sem controle; iniciar novos trabalhos no PC.
- Fazer publicação para testar, repetir fila UNCERTAIN, mudar primário, apagar conteúdo, runners ou credenciais.
- Declarar migração total sem prova do ledger, identidade, idempotência e failover.

## SUCCESS_SIGNAL
- PR #230 sai de draft e é incorporada por merge condicionado ao HEAD; arquivos main não têm on.schedule; workflow_dispatch preservado; verify runner permanece offline; ledger, filas e demais jobs não tocados.
- Recibo UTC e rollback (reversão do merge por nova PR) registrados em finding de encerramento.

## FAILURE_SIGNAL
- Concorrência no HEAD, lease mais antigo ativo, estado runner mudado, alteração em diff, erro de permissão/recusa ou execução inesperada.

## TEST_VALIDITY
Suspensão operacional de dois disparos automáticos dependentes do PC, reversível. Permanecem em aberto a migração dos 3 workflows self-hosted e a homologação dos publicadores externos; esta lease não autoriza mudar primário ou criar nova automação.
