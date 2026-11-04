# Lease — incorporar recibo integral AOI 21 / CORTES
STATUS: RUNNING
AREA: architecture/cortes-ledger-evidence-promotion
DATE: 2026-11-04
LEASE_OWNER: chatgpt-reestruturacao-20261104
LEASE_EXPIRES: 2026-11-04T14:36:55.355Z
BASE_HEAD: 23c9599b4071b7536689677fc420365e3a87cf77
TARGET_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2076
TARGET_PR_HEAD: 706272d612d37ded63f871024dc773e38060a4c0
TARGET_PATHS: test-hub/README.md, test-hub/findings/20261104-cortes-15399-full-memory-readback-and-writer-control.md
BASE_README_BLOB: dfbb27cfc53435ca5eb91c72f633f095b18cf47e
GITLAB_README_BLOB: fb083fea5bff66679979be47dc17cfa16f73e466
GOVERNANCE_MANIFEST: 223433740e807a90
RUN: none
JOB: none
SUPERSEDES: none

BASELINE_PROVEN: integridade integral de 2932006 bytes e SHA-256 já comprovada em executor isolado por PR #2076; 68 UNCERTAIN preservados, 456 confirmed, zero media production upload, RESTORE CLI hosted ainda UNVERIFIED. Clipper PR #232 de leitor QA incorporada; PR #229 CAS writer em draft de outro agente.
FAILED_AVOIDED: rejeitar repetição de SELECT com recusa de segurança; não tocar no banco, secrets, média, Windows, deploy, quota, primário ou branches de outros agentes.
SUCCESS_SIGNAL: merge documental de PR #2076 sem conflito; mesmo SHA de README canônico antes, finding disponível em main, nenhuma mudança em código, fila ou execução.
FAILURE_SIGNAL: HEAD de main alterado antes de mutação, conflito, revisão pendente, ou conteúdo substituído.
TEST_VALIDITY: readback GitHub ref/SHA e PR diff + evidência histórica; não repetir retrieval do snapshot sem nova causa.
ROLLBACK: revert documental isolado, sem impacto no banco. Lease encerrar por finding append-only.
