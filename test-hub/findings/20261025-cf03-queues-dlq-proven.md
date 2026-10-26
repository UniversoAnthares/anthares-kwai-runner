# CF-03 (item fixo 20) — Cloudflare Queues/DLQ, redelivery idempotente real
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-25
RUN: Cloudflare Worker anthares-cf03-qa-r0725 (live authenticated Wrangler)
JOB: R07-CF03-20261025
COMMIT: 183f6a8eda4d2585f6cdd73982984a66df541802
SUPERSEDES: test-hub/findings/20261025-cf03-queues-dlq-running.md
LEASE_AREA: cf03-qa-queues-dlq-exclusive
LEASE_OWNER: ChatGPT-CF03
LEASE_STATUS: CLOSED

## Objetivo e criterio
Posicao 20 CF-03 da ordem fixa R07.6: criar um par Cloudflare Queues + DLQ segregado em ambiente de teste, comprovar redelivery idempotente sem efeitos em publicadores reais. Um evento redelivered deve resultar em no maximo um efeito logico; evento persistentemente falho deve chegar a DLQ. Nenhuma publicacao ou fila CORTES de producao envolvida.

## Escopo real no provedor
Account Cloudflare anthares1 reconhecida via OAuth Wrangler, account_id 5c24be052e5144391f73a8e03491e88e. Worker exclusivo anthares-cf03-qa-r0725, URL https://anthares-cf03-qa-r0725.anthares1.workers.dev/health .
Fonte independente em test-hub/fixtures/cf03/{worker.mjs,wrangler.toml,README.md} desta branch; SHA256 do worker final 33A9113A6F448E028D374E1AF0CF5A08487F5EB7F44409A665F250D2C8731BBC.
Principal Queue cf03-qa-main-r0725 (Cloudflare Queue ID 17cb65c82df14ba5b94eea0aa30fedb0); DLQ cf03-qa-dlq-r0725 (Queue ID 498d0e0165ca4512bc50b8d9b11f3185).
SQLite-backed Durable Object Cf03Ledger exclusivo; tabelas synthetics attempts/effects/deadletter/seeds, PRIMARY KEY por id. Consumer e producer apenas do Worker QA, max_retries=1, batch_size=1, sem bindings com publicadores, tokens sociais, rotas customizadas, cron, SQL/Neon ou armazenamento produtivo.

## Evidencias decisivas na Cloudflare
1. Preflight Windows policy.py PASS (codigo 0) job R07-CF03-20261025, local governance f6fc9ca59a96e451; GitHub main governance 2e28d54043d6bad1 divergente no INDICE.md, sem reconciliacao destrutiva. Test Hub lease em branch exclusiva.
2. Wrangler version 4.149.0. Inicialmente Worker ausente (Cloudflare erro 10007) e Queue list sem queues. Node --check exit 0, Wrangler dry-run exit 0. Criação das duas filas, ambos comandos exit 0. Deploy do Worker exit 0, versão inicial b34341b0-e297-471d-9a40-5bc0cbcf8ce4; reimplantado apos correção do trim da chave temporaria versão f3602d71-47e0-4e4e-ae9e-b272d9782fbb. Readback Queues info: 1 producer + 1 consumer na principal, 1 consumer na DLQ, nomes/IDs esperados.
3. Health HTTPS: ok=true, ledger=true, producer_binding=true, publication_allowed=false, external_destinations=0. POST /__cf03/seed sem chave => HTTP401.
4. Segredo de teste de 32 bytes aleatorio gerado apenas em memoria, configurado na Cloudflare como CF03_RUN_KEY; HTTP POST autorizado => 202, seeded=3, apenas IDs sintéticos fixos; protecao de seed unico gravada em DO. O primeiro ensaio retornou HTTP401 e NAO criou mensagens; causa era propagacao/normalizacao de entrada no CLI, solucionada por trim e nova autenticacao. Sem repeticao cega de mensagem.
5. READBACK REAL DO COM A FILA:
   - cf03-r0725-once: attempts=1, uma linha em effects.
   - cf03-r0725-retry: attempts=2, exatamente uma linha em effects; uma entrega redirecionada a retry APOS registrar primeiro efeito, provando idempotencia em redelivery.
   - cf03-r0725-fail: attempts=2, NENHUMA linha em effects e exatamente uma linha em deadletter; o handler da DLQ recebeu a mensagem apos max_retries=1 da Queue principal.
   - total effects=2, deadletter=1, seeds=1, sem duplicacao de efeito logico.
6. Segredo temporario CF03_RUN_KEY excluido do Worker com wrangler secret delete exit 0; wrangler secret list confirmou ausencia. POST de chave invalida novamente => HTTP401. GET /health e /status seguiram normais. Nenhuma outra credencial alterada.
7. Health do Worker produtivo anthares-control permaneceu ok=true, version=2026-10-17-physical-android-v18, queue_bound=true antes/depois; nenhum job social, feed, API de rede ou publicacao acionada. Nao houve modificacao em fila, banco, codigo/CI de producao, plano contratado ou faturamento.

## Capacidade/limites
Cloudflare Queues disponivel no Workers Free a partir de 2026-02-04. Documentacao oficial vigente indica 10000 operacoes/dia incluidas e 24h de retencao para Free; este teste consumiu poucos eventos (3 mensagens e seus retries), sem aumento de plano. O plano REAL e cobranca da conta anthares1 nao foram auditados pela API de billing, anteriormente 403; nao garantir custo efetivo zero, apenas que nao houve contratacao ou alteracao de billing e o teste ficou no volume gratuito documentado.
Recursos QA identificados permanecem isolados/inativos: sem cron, test seed ja consumido, segredo removido, Worker somente leitura com status e health. Preserve-os como evidencia ate revisao governada. Reaproveitamento exige novo lease/ids e consulta de quota.

## Classificacao
✅ CONCLUIDO no pacote autonomo R07.6 do item 20 CF-03 — Queue/DLQ real e redelivery idempotente sintetico validado, sem efeitos nos publicadores. NAO prova integracao ao ledger canônico/UNCERTAIN do CORTES, iam por conta, cutover de rede nem filas sociais em producao; ISO-04 e SEC-02 continuam gates independentes. Outros 33 estados nao foram modificados por esta prova.
