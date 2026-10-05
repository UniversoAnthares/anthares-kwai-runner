# Final control-plane snapshot validated; production remains stale
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37389453216
JOB: 112030781557
COMMIT: 87921cd9f0e8b9b81ebe92c832a8fe29304b1720
SUPERSEDES: test-hub/findings/20261005-1942-control-plane-no-pc-static-proven.md

## Objetivo
Validar o snapshot final depois do hardening de confirmação, remoção de PC/Google/WordPress e versionamento explícito.

## Resultado
PROVEN no snapshot: fila/ledger fail-closed, PC/local e Google removidos, HLS não possui fallback WordPress hardcoded, versão de produção esperada é 2026-10-05-no-pc-confirmation-v12. O probe read-only continua mostrando que produção ainda está na versão antiga com fallback local.

## Evidência decisiva
Run 37389453216 / job 112030781557: invariantes estáticas SUCCESS e probe de produção HTTP SUCCESS. A comparação confirma snapshot novo válido e produção antiga ainda ativa.

## Consequência
Não confundir health verde com versão correta. Aceitação de deploy deve exigir version=2026-10-05-no-pc-confirmation-v12 e pc_fallback=false. Não repetir Wrangler no runner público sem credencial.
