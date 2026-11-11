# LinkedIn pessoal — última pendência pública resolvida por readback isolado
STATUS: PROVEN
DATE_UTC: 2026-11-11
AREA: linkedin-personal-production-readback
SUPERSEDES: test-hub/findings/lease-20261111-linkedin-personal-readback-production.md
LEASE_STATUS: CLOSED
OWNER: chatgpt-cortes-20261111-readback
BASE_HEAD_AT_CLOSURE: b7ab320465226effad04f568c8c09cd41b194c8a

## Evidência produtiva
- PR #2345 merge b7ab320465226effad04f568c8c09cd41b194c8a: workflow primário já hospedado aceita `workflow_dispatch` com `reconcile_only=true`.
- Live run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43010847897 succeeded.
- Step "Reconcile pending personal posts using public proof, without upload" success, log `PERSONAL_READBACK_ONLY_RECONCILED=1`.
- Step "Retry only distinct Neon jobs; never blindly repost uncertain media" explicitly SKIPPED.
- Neon readback exact ID `cortes-fanout-linkedin-d72c9d334c263fc41181f8a65887b869`: `status=confirmed`; unchanged remote ID `urn:li:ugcPost:7526240278874095616`; evidence `linkedin_public_embed_http200`.
- Aggregate LinkedIn personal after run: 141 confirmed, 245 queued, 6 failed, 0 uncertain. Other agents may advance the queue independently.

## Limite de aceitação
This closes the LinkedIn PERSONAL uncertain backlog observed in this session only. Other destinations remain independent and are NOT certified as complete. No synthetic tests, Neon admin SQL update, browser/PC media, duplicate posting, new secrets or publisher pause. Primary cron remains active; future new accepted posts can temporarily require authenticated public readback.
