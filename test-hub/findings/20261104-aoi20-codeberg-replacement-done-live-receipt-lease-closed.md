# AOI #20 — substituição do espelhamento GitHub→Codeberg pelo Forgejo Hostinger
STATUS: PROVEN
AREA: architecture/aoi20-codeberg-mirror-replacement
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T17:08:53.153Z
ITEMS: [20]
TERMINAL_STATE: DONE
RUN: live-readonly-hostinger-receipt
JOB: none
COMMIT: 300502a7f2eaa3d6cca84732de9e2984d8c19cb6
SUPERSEDES: 20261104-lease-aoi20-codeberg-replacement-close.md
LEASE_OWNER: chatgpt-optimization-20261104
LEASE_AREA: architecture/aoi20-codeberg-mirror-replacement
LEASE: CLOSED
GOVERNANCE_MANIFEST: 223433740e807a90
PRODUCTION_CHANGE: NONE
COST_ADDED: 0

## Critério terminal
Substituir fluxo GitHub→Codeberg pelo espelhamento autorizado, sem loops. O item #17 tem prova terminal de remoção operacional do Codeberg: 27/27 workflows históricos sem cron/push, 28/28 jobs históricos if:false e 13/13 ações Codeberg-only no GitHub inativas, em test-hub/findings/20261028-item17-codeberg-retired-proven.md.

## Provas independentes
- Hostinger sincroniza refs do GitHub para bare Forgejo por git fetch atômico, sem force e sem prune. O workflow GitHub .github/workflows/forgejo-mirror-sync.yml é somente leitor do recibo (blob da43b1d04b6ca14ce5285fc7c5fdbf5307e36f3c), sem escrita de volta ao GitHub; não forma loop.
- Em 2026-11-04, POST read-only https://anthares.us/forgejo-sync.php retornou HTTP 200 e recibo exato SYNC_PROVEN 84bbe614a50e41852f1f6e88deb90a14e8576c64; readback GitHub main no mesmo momento confirmou esse SHA.
- infra/forgejo-proxy/sync.php, blob a8c7397711d057baf771c7e73bcc963ec39e8b7c: recibo datado em até 2400 s, failures=[], no_force=true, no_prune=true, SHA esperado da branch main e comparação com git rev-parse no bare real. Falha fechada (503) em inconsistência; GET retorna 405 conforme contrato.
- Homologação prévia por Github Actions run 40746611827, job 123025502074, em 2026-10-28, registrou HOSTINGER_INDEPENDENT_RECEIPT=PROVEN e CROSS_PROVIDER_SHA_CHECK=PROVEN; restaurou 13 repositórios não vazios e reconheceu 2 vazios, sem alteração dos históricos de outro provedor.
- Consulta atual GET https://anthares.us/forgejo/api/v1/version retornou HTTP 502. O recibo independente do bare espelho retornou 200. Assim, itens #4 e #7 permanecem parciais por funcionamento integral da UI/API pública e auditoria ampla periódica.

## Resultado e limites
Item #20 DONE somente para substituição do espelhamento operacional. Item #13 permanece condicionado por DENIED_PENDING_REVIEW dos históricos GitLab, que não devem ser transportados por nenhuma rota alternativa. Não reivindicar recuperação de todas as origens. Nenhuma publicação social, mudança de production scheduler, token, domínio, runner, banco ou quota; custo adicional zero.
Rollback: revert documental deste finding com SHAs atualizados; manter fontes canônicas e espelhos já autorizados, sem reativar Codeberg.