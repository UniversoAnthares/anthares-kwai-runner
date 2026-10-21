# Lease: política normativa do CLIPPER para Pinterest/LinkedIn e metadados
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-20
RUN: none
JOB: none
COMMIT: 3bf67b7fa4b812ad05229cf4ecb1c6b99a674f80
SUPERSEDES: none
LEASE_AREA: cortes-clipper-distribution-policy
LEASE_OWNER: chatgpt-current-conversation
LEASE_MAX_EXPIRY_UTC: 2026-10-21T00:52:00Z

## Objetivo
Atualizar a política normativa do CLIPPER na branch isolada: Pinterest publica todos os masters curtos elegíveis na rodada, respeitando rate limits reais; LinkedIn mantém 20/dia; metadados de todos os destinos seguem título com sufixo literal e site literal em tags e descrições quando disponíveis.

## BASELINE_PROVEN
GitHub clipper main 3bf67b7fa4b812ad05229cf4ecb1c6b99a674f80, README sha 367225eec4354ce2c5fcd40b4d854e8ce9023b32, quota atual Pinterest 20, LinkedIn 20. Peer GitLab main em 64f51fab9866cb9123acbc0931ed3ea257f4fc5b, divergência de histórico identificada; nenhum espelhamento autorizado.

## FAILED_AVOIDED
Não forçar push, alterar main diretamente, apagar masters, promover a publicação real sem OAuth/conta verificada ou assumir quota ilimitada de API.

## SUCCESS_SIGNAL
PR isolado contendo política escrita e teste/revisão, LinkedIn 20 intacto. Nenhuma alegação de migração de produção sem prova separada.

## FAILURE_SIGNAL
SHA alterado, lease concorrente, requisitos de segurança não satisfeitos.

## TEST_VALIDITY
Somente documentação neste escopo. CI sobre PR confirma integridade documental; runtime é auditoria independente.
