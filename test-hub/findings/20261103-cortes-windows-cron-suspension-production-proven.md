# CORTES — suspensão efetiva de agendamentos Windows/PC em produção
STATUS: PROVEN
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/230
JOB: none
COMMIT: 8c31afffe137a9ed1d9860d10e8c8d380b3a86ec
SUPERSEDES: 20261103-lease-queue-cortes-windows-cron-production-suspension.md
VERIFIED_UTC: 2026-11-03T20:35:48.755Z
GOVERNANCE_VERSION: 223433740e807a90
OWNER: ChatGPT / Reestruturação e Otimização

## Objetivo
Cumprir a suspensão operacional de dois agendamentos de CORTES que requeriam runner Windows no PC pessoal, mantendo código e acionamento manual disponíveis e preservando outras operações.

## Alteração executada
- A PR #230 foi marcada pronta para revisão e incorporada por merge normal ao main de UniversoAnthares/anthares-clipper.
- Merge commit confirmado em main: 8c31afffe137a9ed1d9860d10e8c8d380b3a86ec (2026-11-03T20:32:50Z).
- Removidos somente os blocos on.schedule de .github/workflows/cortes-daily.yml (cron 40 10 * * *) e .github/workflows/cortes-kwai-dispatch-refill.yml (cron */5 * * * *), total de quatro linhas, sem adições.
- SHA dos arquivos no main após merge: daily ab85e4780efc76f3ae3b249a08564924317dd2f5; refill 63151d9d4098fc09363f83eb38d360964d3b012d.
- Os dois workflows têm on.workflow_dispatch preservado e continuam com runs-on self-hosted Windows; o terceiro cortes-short-resume.yml permanece intacto (blob 18f42de7a10571f43dc3e725f462dadda06baf90).
- O runner GitHub de Clipper id 21 DESKTOP-FTDK0HP estava offline, busy=false. No Windows: zero processos Runner.Listener/Runner.Worker/run-svc e zero tarefas de runner habilitadas (2026-11-03).
- O histórico de Actions do Clipper não contém novo run após 2026-10-30; o item 41126324696 segue queued histórico inconsistente e não foi reenviado ou cancelado.
- Os dois arquivos não existem no espelho GitLab do Clipper; nenhuma sincronização manual cega foi feita.

## Critérios verificáveis
PROVEN: os dois CRON Windows foram retirados do main do Clipper. O GitHub deixou de possuir esses gatilhos de agendamento; código, mídia, ledgers e filas foram preservados. Nenhum publicador, trigger manual ou serviço de execução remoto foi ativado por este trabalho.

## Limitações
Esta prova atesta suspensão segura de agendamentos, não migração operacional de produção: os workflows mantêm dependência self-hosted Windows quando chamados manualmente/por push. O fluxo hosted de CORTES tem somente preflight PROVEN em run 41116819377; checkpoint, mídia, identidade, fencing, ledger remoto e publicação real ainda exigem aceite. Portanto o item geral de remoção do PC está PARTIAL.

## Recuperação / rollback
Para restaurar os CRON, abrir uma PR a partir do commit atual com reversão estrita das quatro linhas removidas no merge 8c31afffe137a9ed1d9860d10e8c8d380b3a86ec, após novo lease e verificação de concorrência, quota e owner. Não reativar tarefas locais ou executar publicação apenas para provar rollback.

## Coordenação
O lease de suspensão de 2026-11-03 foi encerrado por este finding. Não iniciar outro executor ou job de CORTES em paralelo para repetir trabalho incerto.
