# CF02 422 source-fix hypothesis abandoned after harness correction
STATUS: ABANDONED
AREA: github, cloudflare
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40319550329
JOB: 121560741631
COMMIT: 00634f88955321cc94a3c480477a1001ff0b535d
SUPERSEDES: test-hub/findings/20261026-cf02-cas-422-fix-running.md
LEASE_AREA: cf02-422-cas-source-fix-exclusive-qa
LEASE_OWNER: ChatGPT-CF02-CAS
LEASE_STATUS: CLOSED

## Razao verificavel
O ensaio inicial #40318473908 causou 422 "Invalid request." apos um GET inicial a QA_PATH no MAIN (arquivo ausente) e um PUT no branch QA (arquivo existente). Como o harness substituiu apenas a branch do corpo JSON, mas nao a query ?ref=main do GET, o PUT nao enviou SHA e o provider retornou erro 422. Este ensaio nunca estabeleceu a precondicao de um CAS stale-SHA; seu resultado sobre o algoritmo produtivo deve ser classificado INVALID/NOT_TESTED, nao FAILED.
O diagnostico #40318947798 imprimiu corpo HTTP422 "Invalid request." (sem erros detalhados). Corrigido UNICAMENTE o harness para reescrever tambem a leitura GET, teste com concorrencia REAL #40319550329 deu SUCCESS e conflito HTTP409 verdadeiro. A source principal .github/workflows/cloudflare-central-deploy.yml nao foi alterada para 422; a hipotese de que precisava ser alterada era falsa. Codigo principal permanece merge PR #1346 SHA 00634f88955321cc94a3c480477a1001ff0b535d, sem rollback nem reenvio social. Nenhuma alteracao no caminho de producao em razao deste ensaio invalido.

## Consequencia
Nao acrescentar retry indiscriminado de HTTP422: 422 e classe generica de validacao e exigiria prova especifica de stale SHA real. Reusar a fixture de teste v4 que consulta SHA na MESMA branch do PUT. O receipt foi integrado ao source main e API GitHub 409 real ja foi comprovado pelo finding test-hub/findings/20261026-cf02-real-provider-cas-proven.md. Lease encerrado; sem mutacao de prod.
