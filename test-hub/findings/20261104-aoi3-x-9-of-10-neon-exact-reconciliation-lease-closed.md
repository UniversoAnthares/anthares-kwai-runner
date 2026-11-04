# AOI #3 — inventário X-PUBLISH reconstituído e reconciliação exata Neon
STATUS: PARTIAL
AREA: architecture/x-neon-ledger-historical-readback
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T21:26:17.734Z
ITEMS: [3]
SUPERSEDES: lease-20261104-aoi3-x-neon-exact-readback.md
LEASE: CLOSED
LEASE_OWNER: chatgpt-aoi3-20261104
SOURCE_MAIN_AT_START: 52030b11b35dbbce48b3cc48734305d94d719694
EXTRA_COST: 0
PRODUCTION_CHANGE: NONE

## Provas independentes
- Github search `repo:UniversoAnthares/anthares-kwai-runner in:title X-PUBLISH`: 12 issues: duas de validação/fixture (#93, #98) excluídas pelo contrato `tools/x_legacy_ledger_inventory.py`; dez issues reais de `duration_class=long` e conta `lucasyahn`: #385, #386, #387, #497, #513, #516, #520, #521, #522, #1002.
- Identidade de cada issue rederivada exatamente conforme `fingerprint()` e `hashlib.sha256('x:lucasyahn:x_'+fingerprint)`, com 3 decimais e ajuste de `scan_start`.
- Neon project `purple-flower-35918989`, tabela `public.anthares_x_submission_ledger`: SELECT read-only com LEFT JOIN sobre **dez hashes SHA256 completos**, resultado exato 9 `confirmed`, 9 `confirmed_at` preenchidos, 9 URLs no formato `https://x.com/lucasyahn/status/...`, 1 `MISSING`. As nove correspondências são #385, #386, #387, #497, #513, #516, #520, #521, #522. Sem outras rows nessa tabela na consulta geral anterior.
- Issue #1002 está OPEN, possui zero comentários e seu SHA256 de idempotência `e2dc272927c55a5308b590396dc152f8a15d0c1c1eef7b75781bd1fa2478a5b4` falta no Neon. A ausência de comments ou row Neon isoladamente não prova `NOT_APPLIED` na origem antiga; classificar como `RECONCILE_REQUIRED`, sem reenvio.
- Origem de ledger antiga Northflank `/x/health` respondeu HTTP 200, `ok=true`, `vault_ready=true`, `backend=local_playwright_vault`. Isto comprova liveness; **não** confirma o estado do `/x/post-status` autenticado para issue #1002. O roteiro existente `tools/x_legacy_ledger_inventory.py` exige ARA_SHARED e checa incidentes STARTED/UNCERTAIN antes de determinar elegibilidade; não foi executado sem seus segredos aprovados.

## Critério restante
Uma consulta autenticada, read-only e autorizada ao ledger Northflank para todos os 10 hashes precisa reconciliar o status da issue #1002 com histórico/recibo de plataforma, preservando `UNCERTAIN`. Somente após reconciliação e provas de identidade, limites, runner Forgejo e end-to-end de publicação segura é possível habilitar `X_LEDGER_MIGRATION_VERIFIED` e promover o novo publicador. Nenhum novo post, tentativa de claim, SQL WRITE, workflow ou deploy foi realizado nesta rodada.

## Resultado
Subtarefa **9 identidades históricas no Neon: PROVEN**. Item fixo #3 permanece PARCIAL pela issue #1002 e promoção do publicador. Preservar escopo do Test Hub e não confundir confirmação Neon com readback atual na rede X.
