# CF-02 — staging isolado de Worker Anthares Cloudflare (preflight)
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-25
RUN: none
JOB: R07-CF02-STAGING-20261025
COMMIT: 183f6a8eda4d2585f6cdd73982984a66df541802
SUPERSEDES: none
LEASE_AREA: cf02-anthares-control-isolated-stage
LEASE_OWNER: ChatGPT-CF02
LEASE_BASE: anthares-kwai-runner/main@183f6a8eda4d2585f6cdd73982984a66df541802
LEASE_SCOPE: worker NOVO e exclusivo anthares-cf02-stage-r0725 sem rotas, cron, KV, DO, secrets, publicador, banco ou fila; rollback so nesse nome; nenhuma escrita nos workers existentes.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
Checklist R07.20: PR draft #1346 CAS de recibo HTTP 409, CI não implantante 40157117628 SUCCESS. CF02 parcial; sem staging/rollback anterior. Fonte index.js no main, SHA blob 74eb9a1c832bdd751c42abc2633bb99305159eaf. Preflight Windows job CF02-STAGING-20261025 f6fc9ca59a96e451 PASS e OAuth Wrangler authenticated com workers_scripts(write), conta Cloudflare reconhecida 5c24be052e5144391f73a8e03491e88e. Fonte GitHub de governança 2e28d54043d6bad1 diverge da copia local no INDICE.md; divergencia preservada.

## FAILED_AVOIDED
Nao modificar worker anthares-control de producao, nao rodar deploy central, cron, cleanup de fila, endpoints de publicacao, secrets, KV ou Durable Objects. Nao repetir job 40151702008 nem usar recusa de outro agente como autorizacao. PR #1346 pertence a outro executor; nao modificar.

## SUCCESS_SIGNAL
Staging de nome exclusivo com source importado do Worker real sem recursos produtivos; health HTTPS 200, estrategia somente leitura, endpoint restrito sem credencial bloqueado; falha 503 controlada apenas no staging; rollback para versao saudavel via identificador do provider; health 200 novamente e versao exata conferida. Producao inalterada.

## FAILURE_SIGNAL
Token insuficiente, Worker existente com mesmo nome, falha de bundling, custo/limite, health inesperado, rollback malsucedido ou side effect: abortar sem escrever recurso alheio; reconciliar Worker de staging exclusivamente, relatar parcial.

## TEST_VALIDITY
Teste funcional real SOMENTE de staging sem bindings de producao. Nao prova equivalencia com producao em Durable Objects, KV, cron, SQL, fila ou publicacoes; nao promove automaticamente CF02 de toda a frota.
