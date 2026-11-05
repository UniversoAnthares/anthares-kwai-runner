# AOI #16 — 67 alertas históricos de infraestrutura/produção reclassificados
STATUS: PARTIAL
AREA: qa-p0-issue-metadata-queued-and-producer
DATE_UTC: 2026-11-05T01:41:38.301Z
ITEMS: [16]
LEASE: CLOSED
LEASE_OWNER: chatgpt-aoi16-issues-20261105
SUPERSEDES: lease-20261105-aoi16-queued-producer-issue-metadata.md
SOURCE_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2106
SOURCE_MERGE_COMMIT: 99d276a8b1900cd882cf95d7375d9eb7cb564032
RUN: GitHub API issue metadata only
JOB: none
ADDITIONAL_COST: 0
PUBLISHER_CHANGE: NONE

## Resultado real
Anteriormente, 56 issues com `Estágio: github_actions_queued_stale` e 11 com `Estágio: P0_DAILY_PRODUCER_ZERO_MASTERS` tinham título `Falha de publicação` e rótulo `publication-failure`. Eram observações da fila/geração anteriores a qualquer prova de envio remoto. O código corrigido pelo PR #2106 mantém prioridades e proteção de idempotência.

Usando Test Hub lease, para cada issue existente a API confirmou previamente estado open, estágio exato, fingerprint 24 hex, label QA-P0 + publication-failure, título de classificação antiga e ação padrão. Somente título, label de falha de publicação e trecho conclusivo de orientação foram alterados. Outras labels, comentários, evidencia, rede, estágio e fingerprints permanecem. Nenhuma issue foi fechada.

**Retificação efetuada:** 66 mutações nesta operação + 1 amostra inicial (#2029) = 67. Receipts do GitHub por issue confirmaram retorno `open`, título esperado, ausência de `publication-failure` e contagem de comentários preservada.

### Audit trail por estágio
- 56 issues de fila/infra: #2010, #2002, #2001, #1986, #1983, #1982, #1896, #1830, #1829, #1814, #1623, #1541, #1540, #1539, #1536, #1535, #1391, #1390, #1389, #1388, #1387, #1386, #1384, #1383, #1154, #1150, #1149, #1147, #1145, #1141, #1139, #1138, #1137, #1136, #1135, #1028, #1022, #1012, #989, #966, #964, #924, #921, #920, #896, #895, #876, #834, #821, #820, #819, #818, #807, #803, #715, #701.
- 11 issues de produção sem masters confirmados: #2029, #1966, #1883, #1500, #1435, #1366, #1060, #955, #774, #716, #610.
- Estágio de distribuição: nenhuma issue anterior encontrada no escopo.

### Readback independente
Após todas as operações, leitura nova de dez páginas `GET /repos/UniversoAnthares/anthares-kwai-runner/issues?state=open&labels=QA-P0&per_page=100&page=1..10`:
```
QUALIFIED_TOTAL=67
QUEUED_STALE=56
PRODUCER_ZERO=11
STILL_OPEN=67
QA_P0_PRESENT=67
PUBLICATION_FAILURE_REMOVED=67
FINGERPRINT_PRESENT=67
EVIDENCE_PRESENT=67
INVALID=0
```

P0s de falhas reais #2044 (Instagram) e #2047 (CORTES fanout) foram reconfirmados como open com seus labels `QA-P0` e `publication-failure` intactos. Os incidentes reais permanecem sob investigação; corrigir classificação e import não comprova sucesso de publicação social.

## Preservação de governança
Nenhum workflow de QA foi reativado. Antes da operação, controlador, watchdog, executor e Instagram auto estavam `disabled_manually`, conforme política do titular. Nenhum job de CI, publicação, retry, segredo, ledger, fila, plano pago ou PC executor foi acionado. Hostinger/Forgejo e o controlador Vercel mantêm bloqueios independentes.

**Resultado:** a subtarefa de reclassificação dos 67 tickets está CONCLUÍDA. Item fixo #16 global permanece PARCIAL até resolver os P0s verdadeiros mediante recibos remotos.
