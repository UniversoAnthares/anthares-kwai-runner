# Lease Anthares Studio — snapshot literal do código G2 (sem ativação)
STATUS: RUNNING
AREA: studio-g2-source-snapshot
DATE: 2026-11-16
START_UTC: 2026-11-16T15:41:00Z
EXPIRES_UTC: 2026-11-16T16:11:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: snapshot literal do plugin original em branch isolada
COMMIT: anthares-wordpress/main=40820c15388f584beca830feec3200a135833b28
SUPERSEDES: none

## BASELINE_PROVEN
- /estudio: plugin original anthares-estudio 0.7.7, hash PHP `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- Backup G1 gravado, restaurado em MariaDB isolado: 217 tabelas, 40+31 posts e 7 Deltas, sem mutação no legado.
- G0 documentação 19 arquivos merged #302; preflight 629/629 e QA PHP PASS.
- Matriz de capturas de interface G1 permanece pendente: G2 restrito a snapshot de código, não a implementação/ativação.

## FAILED_AVOIDED
- Renomear ou ativar o plugin fonte; colisão fatal de prefixos `aest_`; sobrescrever arquivos da origem; criar post em produção; deploy para /studio sem isolamento, ACF/paridade; disparar crons; armazenar trabalho no PC; push em branch compartilhada.

## SUCCESS_SIGNAL
- Branch `feat/studio-g2-raw-legacy-snapshot-20261116` em `anthares-wordpress`, criada a partir do HEAD identificado.
- Todos os 7 arquivos originais em `anthares-studio/` byte a byte com SHA-256 confirmado. PR em DRAFT sem merge/deploy/ativação.
- Manifestos de QA atualizados para cada arquivo auditável e preflight PASS.
- Origem continua com hash idêntico e sem alteração de dados.

## FAILURE_SIGNAL
- divergência de hash; push não autorizado; QA fail; plugin novo ativado/rotas expostas; mudança concorrente de ref; outro lease ativo em mesma área.

## TEST_VALIDITY
Lease de código/snapshot de origem APENAS, não permite aprovação de G2, merge do plugin, ativação, migração de dados ou mudanças em /estudio. G1 visual e homologação continuam requisitos antes de ativar a cópia.
