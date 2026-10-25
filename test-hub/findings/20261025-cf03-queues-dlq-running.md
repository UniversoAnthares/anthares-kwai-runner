# CF-03 — ensaio isolado real de Cloudflare Queues/DLQ
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-25
RUN: none
JOB: R07-CF03-20261025
COMMIT: 183f6a8eda4d2585f6cdd73982984a66df541802
SUPERSEDES: none
LEASE_AREA: cf03-qa-queues-dlq-exclusive
LEASE_OWNER: ChatGPT-CF03
LEASE_BASE: anthares-kwai-runner/main@183f6a8eda4d2585f6cdd73982984a66df541802
LEASE_SCOPE: Cloudflare anthares1, criar somente queues cf03-qa-main-r0725/cf03-qa-dlq-r0725, Worker anthares-cf03-qa-r0725 e ledger Durable Object exclusivo do Worker; mensagens sintéticas; nenhum binding, conta, publicador ou fila real alterado. Código e provas em branch evidence/cf03-queues-dlq-live-20261025.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
R07.6 posição 20 CF-03 PENDENTE; aceite: Queue/DLQ em tenant de teste com redelivery idempotente, sem efeitos em publicadores. CF-02 posição 19 staging de Worker testado e rollback real, sem autorização de cutover; ISO-04 mantém gates de produção. Cloudflare Queues no Workers Free oferece 10000 operações/dia e retenção 24 h (docs 2026-04-21). Conta anthares1 OAuth Wrangler autorizado, listagem queues vazia na conta. Preflight policy.py exit 0, governança local f6fc9ca59a96e451, GitHub main 2e28d54043d6bad1 divergentes; preservar.

## FAILED_AVOIDED
Nenhum deploy em anthares-control ou publicadores, sem cron, rotas personalizadas, banco Neon, segredos de redes, R2, KV produtivo, faturamento, envio de vídeos ou ativação do pipeline CORTES; não efetuar alterações diante de recusa de acesso/administração. Retry e DLQ apenas da queue QA. Não apagar fila de terceiros.

## SUCCESS_SIGNAL
Worker QA real deployed sem acesso a APIs sociais; 3 mensagens sintéticas: sucesso simples, redelivery apos efeito idempotente, falha persistente que entra na DLQ; ledgers SQL (PRIMARY KEY) provam um único efeito lógico por id após >=2 tentativas e um evento DLQ, status remoto HTTPS verificado. Recursos QA podem ser mantidos para evidência se bem identificados, ou eliminados somente depois de provas e sem afetar terceiros.

## FAILURE_SIGNAL
Plano exige assinatura, conta incorreta, deploy ou consumo falha, DLQ não recebe, duplicidade de efeitos, quotas ou publicação inesperada: classificar parcial/failed com evidência, reconciliar antes de repetir; não promover CORTES.

## TEST_VALIDITY
Prova Cloudflare Queues real apenas para recursos sintéticos de staging; prova SQL DO exclusiva do teste, sem efeitos sociais; não homologa integrações de runtime CORTES nem quota/custo da conta e não valida segregação IAM entre identidades.
