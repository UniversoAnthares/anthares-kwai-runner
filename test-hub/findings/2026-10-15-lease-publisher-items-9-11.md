# Lease: consolidate publisher items 9–11
STATUS: RUNNING
AREA: queue
DATE: 2026-10-15
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
LEASE_AREA: queue
LEASE_EXPIRES: 2026-10-15T05:37:00Z

## Objetivo
Fechar os itens 9–11 definidos no estado mais recente: modelo central `Source -> Clip -> Publication`; recuperação/paralelismo com leases, `lease_generation`, TTL/heartbeat/fence e serialização por plataforma+conta; ledger global de deduplicação por intervalo/hash/destino e reconciliação de estado ambíguo.

## Baseline comprovada
- O control plane Cloudflare v16 é a autoridade já PROVEN para enqueue/lease/renew/fencing/crash recovery/UNCERTAIN; não criar outra autoridade de fila.
- O control plane já possui dedupe por chave e overlap temporal PROVEN; o trabalho desta rodada deve consolidar o modelo do publisher e integrar/reusar a autoridade central, não substituí-la.
- Anthares Remote é o único remote; Anthares Browser é o único browser. PC pessoal não é executor normal de publicação.

## FAILED_AVOIDED
Não repetir estratégias retiradas (Render, CircleCI, Browserless/TinyFish sem cota, PC como executor). Não tratar lease expirado depois de `publication_started` como retry-safe. Não fragmentar estado entre uma nova fila SQLite e a fila central.

## SUCCESS_SIGNAL
QA verde cobrindo o modelo canônico, invariantes de dedupe e um contrato de integração que preserve a autoridade do control plane v16; finding final com commits e resultados.

## FAILURE_SIGNAL
Nova store de fila se tornar autoridade concorrente; retry cego de estado UNCERTAIN; dedupe permitir overlap/hash repetido no mesmo destino; testes falharem.

## TEST_VALIDITY
Testes devem executar os módulos reais do repositório no GitHub Actions. Job verde sem as invariantes acima não fecha os itens.
