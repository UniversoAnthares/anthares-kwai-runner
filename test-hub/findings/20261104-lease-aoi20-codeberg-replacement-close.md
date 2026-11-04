# AOI item #20 — lease de recibo do espelhamento substituto
STATUS: RUNNING
AREA: architecture/aoi20-codeberg-mirror-replacement
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T17:07:50.208Z
LEASE_OWNER: chatgpt-optimization-20261104
LEASE_EXPIRES: 2026-11-04T17:27:50.210Z
BASE_HEAD: 84bbe614a50e41852f1f6e88deb90a14e8576c64
GOVERNANCE_MANIFEST: 223433740e807a90
ITEMS: [20]
RUN: none
JOB: none
SUPERSEDES: none

BASELINE_PROVEN: Codeberg retirado da autoridade operacional, item #17 DONE no finding 20261028-item17-codeberg-retired-proven.md. Fluxo GitHub→Hostinger Forgejo documentado no finding 20261028-forgejo-mirror-cdn-readback-verified.md e no workflow main de SHA da fonte da prova. O endpoint POST /forgejo-sync.php é somente leitura no código PHP, com checked_utc de no máximo 2400s, failures=[], no_force=true, no_prune=true, verificação de SHA atual do repo bare. Na leitura ao vivo retornou HTTP200 SYNC_PROVEN 84bbe614a50e41852f1f6e88deb90a14e8576c64; GitHub main lido SHA 84bbe614a50e41852f1f6e88deb90a14e8576c64. O GET indevido retorna 405 conforme contrato. O endpoint público /forgejo/api/v1/version retorna 502, independentemente da sanidade do recibo do bare mirror.
FAILED_AVOIDED: Não tentar reiniciar Codeberg nem reativar workflows desabilitados; não fazer push GitLab recusado, nem deploy domínio/Forgejo, não executar CI de publicação nem alterar jobs ou quotas.
SUCCESS_SIGNAL: registrar DONE exclusivamente do item20, readback do finding em main e branch SHA. Item7 permanece PARTIAL devido a recuperação/observabilidade ampla e HTTP502 da UI do Forgejo.
FAILURE_SIGNAL: HEAD divergir, recibo mudar sem prova, escopo além de item20.
TEST_VALIDITY: GET de health e POST de recibo explicitamente sem mutação, SHA GitHub lido via API. Não invocar novo sync.
ROLLBACK: revert documental da PR, sem efeitos em ambiente de produção.
