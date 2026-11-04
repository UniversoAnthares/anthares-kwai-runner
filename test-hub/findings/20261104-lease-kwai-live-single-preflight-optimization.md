# OTIMIZAÇÃO / AOI #5, #8 — Kwai LIVE: preflight único
STATUS: RUNNING
AREA: kwai-live/workflow-static-optimization
DATE: 2026-11-04
LEASE_AREA: kwai-live-workflow-single-preflight
LEASE_OWNER: chatgpt-optimization-20261104
LEASE_UNTIL: 2026-11-04T13:42:47.618Z
BASE_HEAD: c766e6d7e83d054886667f1450de5ba1e6c0c796
TARGET: .github/workflows/kwai-live-6h.yml
BASE_BLOB_SHA: bb8f66f4ed36f2285183de92b983b1269a80c115
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none
GOVERNANCE_MANIFEST: 223433740e807a90

BASELINE_PROVEN: O workflow manual possui 30 preflights que repetem a mesma autenticação e verificação HLS. O contrato de seis horas ainda não está homologado.
FAILED_AVOIDED: Não executar a LIVE, não disparar Actions, não alterar segredo, cron, sessão, publicador, fila ou Cloudflare.
SUCCESS_SIGNAL: Apenas um preflight; on.workflow_dispatch e gate manual de canário preservados; nenhuma referência matrix.replica; sem alteração de jobs de publicação.
FAILURE_SIGNAL: perda do gate, runner diferente, segunda execução, base divergente.
TEST_VALIDITY: verificação estática isolada de YAML e invariantes, sem rede de mídia.

Alteração proposta: reduzir 30 para 1 job de preflight por acionamento, eliminando 29 jobs redundantes (96,7% do estágio). Código de LIVE contínua permanece pendente de autenticação e aceite remoto.
Rollback: reverter patch da feature branch; sem efeito em produção.
