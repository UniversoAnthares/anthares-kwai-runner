# CORTES-ISO-04 — QA real (SET ROLE) e gate de LOGIN direto
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-25
RUN: Anthares Remote a4fde4a2e96ab13b4ee5233643c4772f (preflight inicial incorreto), 9fba5bbb5fd53b4bea0fc4017d954080 (preflight aprovado), 3dc01bed64227f0cc54efa8669ecfb6d (teste 16/16)
JOB: cortes-iso04-20261025
COMMIT: 1c0c48272f00ac924c300138b6b67473489b5476
SUPERSEDES: none

## Objetivo
Item fixo 09 R07.6: isolar UMA conta por LOGIN PostgreSQL operacional NOBYPASSRLS e provar negativas SELECT/INSERT/UPDATE/DELETE em QA.

## Baseline, falha evitada, validade
BASELINE_PROVEN: QA Neon purple-flower-35918989/br-quiet-unit-b8w1tqmf tem tabela artificial public.cortes_rls_canary_20261024 com ENABLE/FORCE RLS e duas policies escopadas.
FAILED_AVOIDED: criação de LOGIN pelo Neon gerou BYPASSRLS/CREATEROLE/CREATEDB em 24/10; ALTER ROLE foi negado. Não repetir a alteração negada por outro canal. Branch QA adicional solicitada nesta rodada não foi criada; não repetir sem diagnóstico.
TEST_VALIDITY: Neon read-only no estado real de QA, contra quatro registros sintéticos existentes. Testes de código em staging temporário Windows, sem tokens, sem publicação, sem mudanças de dados ou papéis.

## Resultado
- SELECT via transação SET LOCAL ROLE cortes_threads_executor_qa: 2 próprios e 0 Instagram. Instagram sob seu papel: 2 próprios e 0 Threads.
- pg_roles: ambos NOLOGIN, NOBYPASSRLS, NOSUPERUSER, NOCREATEDB, NOCREATEROLE. has_table_privilege DELETE=false e CREATE schema=false.
- RLS produção public.cortes_publications: false, FORCE false, zero policies. Não foi modificada.
- Gate offline novo, PR privada anthares-clipper #204, exige login direto sem SET ROLE, privilégio mínimo, políticas USING/WITH CHECK e negativas reais SELECT/INSERT/UPDATE/DELETE; 16 testes Python OK em Windows, exit 0. Por projeto, gate de observações não equivale a assinatura/atestação independente de origem.
- Logs/artefatos temporários do staging removidos. Nenhum worker, ledger, trigger, senha, principal, deploy ou publicação foi modificado.

## Critério não satisfeito / pendências
FAILURE_SIGNAL: login operacional seguro e sessão autenticada distinta continuam AUSENTES. Os testes de escrita anteriores via SET ROLE não substituem prova por LOGIN; DELETE negativo em sessão autenticada não foi executado.
SUCCESS_SIGNAL: conexão direta com conta de QA NOBYPASSRLS sem DDL, session_user=current_user do executor, com 4 operações cruzadas NEGADAS e conferência imutável do estado; credencial própria protegida, evidência de um controlador confiável e rollback.
CORTES-ISO-04 mantém status PARCIAL. Não ativar RLS em produção nem promover publicadores.

## Recuperação
Rollback do código: fechar PR draft #204. Banco/produção não possuem mudanças desta rodada, rollback operacional N/A. Preservar recursos QA existentes, que podem ser usados por outros agentes.
