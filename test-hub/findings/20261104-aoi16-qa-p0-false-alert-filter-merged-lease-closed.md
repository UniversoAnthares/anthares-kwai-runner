# AOI 16 — filtros de alarmes falsos incorporados, lease encerrada
STATUS: PARTIAL
AREA: qa-p0-nonpublisher-false-alerts
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T14:31:05.808Z
RUN: none
JOB: none
COMMIT: 892fbae82115d04770f051d0677aa42d2e9e9f8e
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2015
SUPERSEDES: 20261104-lease-aoi16-qa-p0-false-alarm-merge.md
LEASE_OWNER: chatgpt-reestruturacao-20261104
LEASE_AREA: qa-p0-nonpublisher-false-alerts
LEASE: CLOSED
GOVERNANCE_MANIFEST: 223433740e807a90

## Feito e evidência
Merge da PR #2015 confirmado no main SHA 892fbae82115d04770f051d0677aa42d2e9e9f8e. Arquivos observados em main: tools/cortes_qa_p0_router.py blob 3c0f0e146eb02787d415155bddf968a0d04f093d, .github/workflows/cortes-qa-p0-publication-watchdog.yml blob fe5bd583a37e0d6545d60ca50124c9c41b508c35, tests/test_cortes_qa_p0_router.py blob 5becb656c040fb1d6fbb53d4de78594cb160ade2.
Readback da regex exata em main: 5 nomes de preflight/auditoria/recuperação classificados como não-publicadores; 3 nomes de publicação real preservados. QA prévia registrada em 20261031-qa-p0-filter-targeted-execution-partial.md: 8/8 Python e 9/9 JS em sandbox. Este round conferiu somente invariantes estáticos, não alegar novos testes integrados.
Nenhum cron novo, nenhuma mídia publicada, nenhum lease de publicação, alterações em Neon, Cloudflare, contas, runners Windows, permissões ou credenciais. Custo adicional zero.

## Aceite restante
Item AOI #16 segue PARTIAL: aguarda leitura de nova execução hospedada do controlador de incidentes e confirmação de ausência de alertas falsos com detecção mantida das falhas reais; resolver causas reais dos incidentes existentes e registrar recibos. GitHub Actions não mostrou runs recentes neste repositório após 2026-11-01 pela consulta atual; hipótese de quota/status permanece pendente. Não reiniciar CI ou abrir incidentes sintéticos apenas para testes.
Rollback: PR de revert restrito ao commit 892fbae... mediante HEAD e coordenação.
