# AOI 16 — 32 alertas de infraestrutura reclassificados com estado original preservado
STATUS: PARTIAL
AREA: qa-p0-infrastructure-misclassification
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T17:55:08.222Z
ITEMS: [16]
LEASE_OWNER: chatgpt-reestruturacao-20261104
LEASE_AREA: qa-p0-visibility-incident-metadata-reconciliation
LEASE: CLOSED
GOVERNANCE_MANIFEST: 223433740e807a90
BASE_HEAD: b1e8637be26e7052713dd3af7bd919debab2b90c
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2099
RUN: read-only issues metadata and existing PR source; no CI
JOB: none
ADDITIONAL_COST: 0
SUPERSEDES: 20261104-aoi16-qa-visibility-classification-partial-lease-closed.md

## Escopo concluído
PR #2099 em main b1e8637be26e7052713dd3af7bd919debab2b90c separou o stage `qa_visibility_lost_*` dos incidentes reais de publicação. Um erro de observabilidade gera label somente QA-P0, título `[infra]`, e instrução de recuperar fonte; falhas reais conservam label `publication-failure`, reconciliação e idempotência. Dois testes novos de regressão anexados ao código, mas ainda sem CI remoto; testes dirigidos isolados em fixture 4/4 PASS.

## Recibos remotos de reclassificação
Somente metadados de issues existentes (título, labels e trecho conclusivo de diagnóstico), preservando fingerprint, provas, comentários, identidade e state=open.
- GitHub Actions repo secundário, stage `qa_visibility_lost_github_repo`: 18 issues reclassificados (#2045, #2028, #1928, #1890, #1843, #1729, #1469, #1456, #1407, #1335, #1263, #1140, #1042, #939, #760, #703, #438, #359).
- WordPress QA, stage `qa_visibility_lost_wordpress`: 13 issues reclassificados (#1929, #1844, #1465, #1406, #1334, #439, #346, #1264, #1160, #1153, #956, #775, #702).
- Auditoria GitHub geral, stage `qa_visibility_lost_github`: 1 issue reclassificado (#345).
- Consulta GitHub após mutações: zero issues abertas com o stage `qa_visibility_lost_github_repo`, `qa_visibility_lost_wordpress` ou `qa_visibility_lost_github` e label `publication-failure`. Fonte: search_issues, repo UniversoAnthares/anthares-kwai-runner, data 2026-11-04.
- Alertas técnicos permaneceram abertos e apontam recuperar visibilidade; os comentários antigos, incluindo 102 do #346 e 107 do #345, foram mantidos. Nenhum issue de falha real de publicação foi fechado.

## Aceite ainda pendente
AOI #16 permanece PARTIAL: incidentes P0 reais em CORTES/Threads/Pinterest/X e upload Kwai continuam abertos, sem confirmação causal. A correção apenas encerra os falsos rótulos de erro de publicação. Próxima ação: leitura de logs e prova de correção de cada incidente real, respeitando leis de segurança e sem reenvio cego de UNCERTAIN.
Rollback: reverter a PR #2099 somente após verificar SHA, ou reclassificar metadados individualmente preservando comentários, leases e estados.