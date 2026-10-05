# Lease queue: confirmação positiva fail-closed
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: queue-invariant-hardening
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: queue
LEASE_EXPIRES: 2026-10-05T23:59:00Z

BASELINE_PROVEN: lifecycle central enqueue/lease/started/complete/fail/reconcile e UNCERTAIN já existem; QA finding 20261005-1935 identificou confirmação prematura possível.
FAILED_AVOIDED: não confiar apenas no chamador; não alterar agentes de interface; não aceitar complete positivo antes de started nem reconcile positivo fora de uncertain.
SUCCESS_SIGNAL: complete confirmado exige leased + publication_started=1 + evidência positiva; reconcile confirmado exige uncertain + evidência positiva; self-test rejeita transições prematuras e preserva fluxo válido.
FAILURE_SIGNAL: simulação encontra caminho que marca published sem started/uncertain/evidência, ou fluxo válido deixa de completar.
TEST_VALIDITY: validação estática/simulada precisa executar em runner público; deploy production continua separado.

## Objetivo
Fechar no próprio controlador as invariantes de confirmação positiva apontadas pelo QA.
