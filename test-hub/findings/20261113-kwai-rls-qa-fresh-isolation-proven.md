# Neon Kwai: RLS por conta homologado em ramificação recente
STATUS: PROVEN
AREA: kwai
DATE: 2026-11-13
RUN: Neon SQL transaction via connected MCP, read-only verification
JOB: none
COMMIT: fd3302313d4cf52a628adeb871d4c18236e516d9
SUPERSEDES: none
TEST_VALIDITY: PROVEN in isolated QA; production deployment NOT_TESTED

## Baseline
Project anthares-ara-ha, project_id purple-flower-35918989, production branch br-crimson-unit-b89nau08. Production public.cortes_publications: 3,092 rows, RLS false, zero policies, owner neondb_owner (rolbypassrls=true). Runtime infra/neon-cortes-queue/index.mjs connects with injected DATABASE_URL owned by neondb_owner; changing RLS alone would give false security. The table serves Kwai, Instagram, Threads and other platforms.

## Change isolated from production
Created dedicated current-production clone br-plain-surf-b8vupkq8 (qa-cortes-rls-20261113-dual-kwai) on November 13 at ~20:02 -04. Its initial 3,092 rows matched production, including 747 Kwai records. On that QA branch only:
- CREATE ROLE cortes_kwai_primary_rls_qa NOLOGIN NOBYPASSRLS
- CREATE ROLE cortes_kwai_secondary_rls_qa NOLOGIN NOBYPASSRLS
- Grant public schema USAGE plus SELECT, INSERT, UPDATE on public.cortes_publications, without DELETE
- CREATE POLICY for each role FOR ALL, USING + WITH CHECK equal to that account's canonical target_key
- ALTER TABLE public.cortes_publications ENABLE ROW LEVEL SECURITY
- GRANT test roles TO neondb_owner solely to permit SET LOCAL ROLE verification in one transaction
No row DELETE/UPDATE/INSERT was performed by the QA test; 3,092 source rows preserved. Production RLS remained false and zero policies.

## Evidence
One transaction per role: SET LOCAL ROLE then SELECT count/visibility and has_table_privilege DELETE.
- current_user cortes_kwai_primary_rls_qa: visible_rows=640, other_rows=0, other_platforms=0, can_delete=false
- current_user cortes_kwai_secondary_rls_qa: visible_rows=106, other_rows=0, other_platforms=0, can_delete=false
- QA catalog: relrowsecurity=true, 2 pg_policies, relforcerowsecurity=false; table 3,092 rows.
- Production catalog readback: relrowsecurity=false, 0 policies.
These checks validate real Postgres RLS with the correct invoker. They do not prove that the existing Neon Function runs under either constrained role.

## Production promotion gate
1. Inventory ALL consumers and SQL operations on shared table; preserve Instagram, Threads, LinkedIn and other consumers.
2. Create dedicated NOBYPASSRLS login roles (secrets generated and stored in approved secure environment, never printed here). No owner/BYPASSRLS connection may be used for claimed tenant-isolated paths.
3. Route every Kwai query to the correct target-specific connection for the entire SQL transaction; test auth-failure, wrong-account, SELECT/UPDATE/INSERT and dedupe in a fresh QA Function. Keep fail-closed; no actual post in tests.
4. Only then promote policies and app credential routing in controlled steps with rollback, positive and negative tests, and active publication lease fencing. Never toggle FORCE ROW LEVEL SECURITY on shared table without inventory of owners and all platforms.
5. Health stays rls_attested:false / network_isolation:false until fully proven end-to-end in production.

Cost guard: no paid resources, no alteration of production credentials, no new network accounts or Android runtime.
