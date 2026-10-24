# CORTES — verificador de papéis SQL não privilegiados (read-only) comprovado
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-24
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/195
JOB: ChatGPT offline isolated Python tests
COMMIT: 8bdadaac9370c709b0fdfaa12667bb992a5ca08e
SUPERSEDES: test-hub/findings/20261024-1717-lease-cortes-role-capability-gate.md
LEASE_AREA: clipper-ci-neon-role-capability
LEASE_OWNER: ChatGPT current conversation
LEASE_STATUS: CLOSED

## Objetivo
Ajustar aceitação de papéis PostgreSQL para rejeitar runtime roles com CREATEDB/CREATEROLE mesmo se outras afirmações do executor forem favoráveis; preservar fail-closed e contrato deployment_authorized=false.

## BASELINE_PROVEN
Clipper main anterior 7296299623d81236024e3cadbef734b0fd2c901d. Blobs prévios audit 3f96d3917b7770bb481709cbd589f1357cf5f02b, testes 719e7b15606c5f1d0875a6394f790b07a3f04015. Banco Neon QA mostrou que create_postgres_role gerencial cria login com BYPASSRLS=true/CREATEDB=true/CREATEROLE=true. ALTER ROLE de revogação foi negado; os dois logins QA novos e não utilizados foram eliminados e a ausência confirmada. RLS produtiva permaneceu inalterada.

## FAILED_AVOIDED
Nenhum controle Windows remoto, produção SQL, criação persistente de LOGIN, acesso ao handoff Threads, replay de uncertain, promoção de publicadores ou interferência no lease paralelo test-hub/findings/20261024-1704-lease-cortes-neon-qa-runtime-health.md.

## SUCCESS_SIGNAL
PR #195 https://github.com/UniversoAnthares/anthares-clipper/pull/195 merged em 8bdadaac9370c709b0fdfaa12667bb992a5ca08e, arquivos alterados apenas ci/network_neon_isolation_audit.py e tests/test_network_neon_isolation_audit.py. source SHA c89cee2f05a6d0babe8fbdd983b39b229bd43922, tests SHA 126da3122e2acbefd3707fdb851785fac854d083. Fonte é read-only e sempre deployment_authorized=false. As novas checks exigem can_create_database is False e can_create_role is False, e rejeitam ausência dos campos. Testes Python reais de arquivos com EXATAMENTE esses dois hashes Git: Ran 18 tests in 0.001s, OK; compileall ci/tests OK; staging local descartado. Readback main confirmou blobs e merge.
Auditoria SQL apenas metadados das roles NOLOGIN QA confirmou ausência de BYPASSRLS, CREATEDB/CREATEROLE, propriedade do ledger, DELETE no canário e acesso à tabela real do handoff. Tais roles não permitem LOGIN e não mudaram o serviço produtivo.

## FAILURE_SIGNAL
Identidade real de runtime com BYPASSRLS/CREATEDB/CREATEROLE ou privilégio para alterar schema; missing role attestation; DB RLS false ou policy cross-target; sem prova separada de credenciais. O gate não pode aprovar nenhuma dessas condições.

## TEST_VALIDITY
PROVEN apenas como contrato executável offline sobre blobs exatos. Não comprovam CI integral de release, autenticação SQL separada, automações Windows, SQL RLS de produção, escritos únicos, atestação editorial ou publicação canária. Nenhum teste de suíte com negativa anterior foi executado. O lease qa-cortes-neon-health-runtime de outro agente permanece independente.

## Consequência
Lease fechado. Cualquier novo trabalho exige novo Test Hub lease. Nunca criar LOGIN pelo gerenciador Neon e tratá-lo como restrito sem ler pg_roles; aceitar somente rolbypassrls=false, rolcreatedb=false, rolcreaterole=false, rolcanlogin=true e políticas atestadas. Controles completos seguem fail-closed.
