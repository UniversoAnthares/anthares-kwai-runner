# Anthares Studio — lease de preparação G1 (baseline e backup isolado)
STATUS: RUNNING
AREA: studio-g1-backup
DATE: 2026-11-16
START_UTC: 2026-11-16T15:23:00Z
EXPIRES_UTC: 2026-11-16T15:53:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: G1 backup/inventário e QA da documentação
COMMIT: 808d2968f8a869ff32b95c59ab356d370d3732e9 (anthares-wordpress/main)
SUPERSEDES: none

## BASELINE_PROVEN
- /estudio ativo, plugin original anthares-estudio 0.7.7; hash PHP `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- 40 posts internos `aest_*`, 31 lixeira; zero posts `anst_*` e zero metadados `_anst_*` na consulta de 16/11.
- PR documental #302 no anthares-wordpress, commit `f776af9c102c0bbcfc96decf5ada0afb4a60dd46`; branch principal intacta.
- Backup externo da migração 15/11 historicamente PROVEN no Test Hub, porém localização/restauração atual não comprovadas em 16/11.

## FAILED_AVOIDED
- Cópia do plugin sem baseline íntegro; mutação no código do legado; backup indiscriminado dos 15GB de uploads; manipulação de registros de usuários; restauração destrutiva do banco compartilhado; criação de novo `anst_*` antes do gate; gravações no PC do titular.

## SUCCESS_SIGNAL
- G1: backup em espaço privado externo, com hashes, inventário completo dos CPTs e prova de leitura/restauração isolada. Sem alteração de `aest_*`; documentação da execução preservada e verificável.
- QA documental: preflight da matriz/manifests concluído e relatado com ambiente/SHA.
- Cada escrita isolada no escopo G1; nenhum deploy ou publicação /studio.

## FAILURE_SIGNAL
- Hash original alterado, status HTTP/probe divergente, backup incompleto, erro no teste de restauração, data race, divergência de HEAD, outro lease com precedência, operação fora do escopo.

## TEST_VALIDITY
São permitidos levantamentos apenas-leitura em paralelo. Escritas autorizadas por este lease restringem-se a backup/snapshot isolado, registros técnicos de evidência e artefatos temporários externos de QA. O lease não autoriza G2 (cópia nem ativação), migração de usuários, alteração de WordPress ou merge de código funcional.
