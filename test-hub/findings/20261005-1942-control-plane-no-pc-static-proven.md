# Control plane sem PC e invariantes centrais validadas
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388406583
JOB: 112027374829
COMMIT: aec5dc04bc5655d7e6ab3da88b8202dfcfcf3733
SUPERSEDES: test-hub/findings/20261005-1930-lease-cloudflare-control-hardening.md

BASELINE_PROVEN: AntharesQueue/Durable Object existente com lifecycle e dedupe.
FAILED_AVOIDED: PC/local não permanece como fallback morto porém operacional; Google/Oracle não entram na prioridade; deploy não é alegado sem credencial.
SUCCESS_SIGNAL: validação independente do snapshot confirma fila/lease/started/complete/fail/reconcile, dedupe temporal, OIDC TikTok, ausência de local/Google e failover Render->GitHub->none.
FAILURE_SIGNAL: qualquer invariante ausente ou fallback local/Google detectado.
TEST_VALIDITY: workflow precisa executar em runner público e concluir o step de invariantes.

## Objetivo
Endurecer o control plane existente para a arquitetura PC-off definitiva e validar invariantes de segurança sem depender do deploy Cloudflare.

## Resultado
PROVEN no snapshot de código: prioridades agora são cuts Render->GitHub, TikTok Render->GitHub, Kwai GitHub, Kwai LIVE HLS origin->GitHub e control Cloudflare->GitHub->Render. Local/PC foi removido das prioridades, probes, credenciais legadas e enqueue específico; heartbeat local retorna retired. Google probe removido. Failover self-test termina em nenhum executor após Render+GitHub indisponíveis, sem cair no PC. O limite diário usa a mesma fronteira America/Campo_Grande.

## Evidência decisiva
Run 37388406583, job 112027374829: step Validate central safety invariants SUCCESS. Snapshot contém AntharesQueue, enqueue/lease/started/complete/fail/reconcile, timeline overlap, UNCERTAIN, OIDC read allowlist e ausência de LOCAL_EXECUTOR/GOOGLE_HEALTH_URL/ANTHARES_LOCAL_HEALTH_URL.

## Consequência
Não reintroduzir PC/local, Google ou Oracle no roteamento. Isto prova o código/snapshot, NÃO o deploy. Produção continua bloqueada até deploy real do Worker com credencial Cloudflare disponível em executor remoto.
