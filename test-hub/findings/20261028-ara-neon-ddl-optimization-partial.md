# ARA Neon: reduzir DDL em requisições
STATUS: PARTIAL
AREA: queue / ara-neon-cost
DATE: 2026-10-28
SUPERSEDES: test-hub/findings/20261028-ara-neon-ddl-optimization-lease.md
COMMIT: 2f14beff2985b26647ecb946bfefa7b1cef42578
BASELINE_PROVEN: schema do Neon main contém ara_reserve_jobs_status_check, ara_reserve_jobs_dedupe e ara_oauth_consumed. Vercel produção no SHA 4494ea971df658b5ae934c3c233936346cfdd678; mudanças desse outro agente preservadas.
RESULT: branch isolado removeu 18 linhas de DDL no router-entry e a verificação de esquema a cada requisição no router; schema continua assegurado nos fluxos OAuth onde necessário. Readback de ambas as alterações confirmado; nenhuma produção alterada.
SUCCESS_SIGNAL: deploy posterior de commit reconciliado com produção e monitoramento de conectividade, status, OAuth, leases, replay e CU-horas.
FAILURE_SIGNAL: falha de operação real ou regressão de autenticação.
TEST_VALIDITY: patches são apenas remoções de DDL de rotina; preservados SAFE_RETRY, uncertainty, leaseNext, createJob, consume, results e fluxos OAuth.
ROLLBACK: manter Vercel dpl_2ew3WQvu8W2n3utFUKHMPGHRQ7Rb até implantação homologada; reverter os dois blobs em nova versão se necessário.
OWNER: ChatGPT GPT-6; lease encerrado após preparar o código.
