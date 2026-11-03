# Lease — revisão dos CRON Windows CORTES / PC fora da execução
STATUS: RUNNING
AREA: queue
DATE: 2026-11-03
RUN: none
JOB: patch-review-only
COMMIT: 9ee0b7c2501c4bf223bbed4203c8a06f3fe9ca46
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / REMOTE-ADMIN
LEASE_START_UTC: 2026-11-03T20:10:14.044Z
LEASE_EXPIRES_UTC: 2026-11-03T20:35:14.044Z
SCOPE: preparar branch e PR isolada no anthares-clipper removendo apenas schedule dos workflows cortes-daily.yml e cortes-kwai-dispatch-refill.yml; preservar workflow_dispatch, código de publicação e ledgers. Sem merge ou alteração operacional de produção.

## BASELINE_PROVEN
- Governança Anthares manifest 223433740e807a90: PC pessoal proibido como executor operacional; custo adicional zero.
- GitHub anthares-clipper main HEAD 9ee0b7c2501c4bf223bbed4203c8a06f3fe9ca46; três workflows ativos dependem de self-hosted Windows.
- Único runner do Clipper: DESKTOP-FTDK0HP offline, busy=false; consultas do GitHub em 2026-11-03.
- cortes-kwai-dispatch-refill.yml cron */5 * * * * e execução com C:\\Users\\Lucas\\AppData\\Local\\Programs\\Python; 557 runs históricos, últimos de 2026-10-30 falhos. cortes-daily.yml cron 40 10 * * * e últimos runs falhos. Nenhum job ativo observado.
- Teste hospedado somente-leitura: run 41116819377 em 2026-10-30, com log CORTES_HOSTED_CANONICAL_SOURCE=PASS e CORTES_HOSTED_READONLY_GATE=PASS; produção/ledger ainda pendentes.
- GitLab espelho do Clipper está defasado e carece destes workflows; não espelhar cegamente.

## FAILED_AVOIDED
- Não desligar publicadores e nem migrar produção antes de checkpoint, ledger, autenticação, idempotência e quota remota comprovados.
- Não reexecutar CORTES, publicar mídia, alterar filas, eliminar dados ou utilizar o PC como staging/runner.
- Não escrever diretamente em main: ruleset proteger-main exige pull request.

## SUCCESS_SIGNAL
PR de dois arquivos com somente remoção dos dois eventos schedule; gatilhos manuais e lógica preservados, revisão sem merge; nenhum novo job criado.

## FAILURE_SIGNAL
HEAD concorrente, lease anterior ativo, bloqueio de provedor, SHA incorreto, arquivo inesperado, alterações adicionais ou trigger involuntário.

## TEST_VALIDITY
Esta lease autoriza apenas proposta em branch isolada com PR. A remoção real dos cron depende de aprovação/merge após análise do owner. O resultado não equivale a migração de produção.
