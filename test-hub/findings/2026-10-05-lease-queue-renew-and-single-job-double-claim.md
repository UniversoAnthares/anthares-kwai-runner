# Lease: queue renew + single-job double-claim
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

## Objetivo
Fechar duas lacunas contratuais do control plane v12 sem alterar os invariantes já PROVEN: renovação explícita e autenticada do lease do job pelo owner atual; e prova de concorrência em que dois consumidores disputam exatamente um único job e existe exatamente um vencedor.

## BASELINE_PROVEN
Cloudflare control plane v12 está PROVEN EM PRODUÇÃO segundo test-hub/README.md: Durable Object SQLite, enqueue/lease/started/complete/fail/reconcile, UNCERTAIN, dedupe, circuit breaker, confirmação fail-closed e roteamento sem PC.

## FAILED_AVOIDED
Não reabrir deploy por runner público sem CLOUDFLARE_API_TOKEN. Não alterar failover, sessão TikTok, login/publicação Kwai nem mecanismos já PROVEN. O teste de double-claim será isolado e deverá alcançar o mesmo precondition para ambos os consumidores.

## SUCCESS_SIGNAL
1. Operação renew aceita somente owner autenticado do job ainda leased e estende lease_until para frente.
2. Renew por owner diferente, job fora de leased ou lease já expirado falha fechado.
3. Self-test cria exatamente um job concorrível e duas tentativas de lease; exatamente uma recebe o job e a outra recebe null.
4. Self-test completo permanece ok=true.

## FAILURE_SIGNAL
Qualquer violação de ownership/estado/expiração no renew, dois vencedores para um único job, zero vencedores com harness válido, ou regressão de self-tests já existentes.

## TEST_VALIDITY
Teste deve usar job isolado/identificador único e limpar/encerrar seu próprio estado. Falha de autenticação externa, deploy ou harness será INVALID/NOT_TESTED e não contará contra a hipótese.

## Lease
MUTATION_AREAS: queue, cloudflare-control
EXPIRES: 2026-10-06T00:35:00Z
