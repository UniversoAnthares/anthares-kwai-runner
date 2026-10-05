# Lease cloudflare-control: remover PC e endurecer invariantes centrais
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: static-hardening
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: cloudflare-control
LEASE_EXPIRES: 2026-10-05T23:58:00Z

BASELINE_PROVEN: controlador central existente com Durable Object SQLite, fila, lease, started/complete/fail/reconcile, heartbeat e routing persistido.
FAILED_AVOIDED: não repetir deploy sem CLOUDFLARE_API_TOKEN; não alterar agentes de interface/publicação; não criar segundo controlador.
SUCCESS_SIGNAL: fonte central não contém PC/local em prioridades de seleção; self-test cobre timezone diário e invariantes de confirmação/reconciliação; análise estática independente passa.
FAILURE_SIGNAL: algum caminho automático ainda seleciona local/PC, ou confirmação/reconciliação permite transição insegura.
TEST_VALIDITY: esta rodada valida código/simulação; não será classificada DEPLOYED sem Wrangler e Worker real.

## Objetivo
Endurecer o controlador existente contra fallback local e fechar invariantes centrais enquanto o deploy real está bloqueado por credencial ausente.
