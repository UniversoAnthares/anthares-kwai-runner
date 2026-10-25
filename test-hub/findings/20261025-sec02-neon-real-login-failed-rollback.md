# SEC-02: dois principals SQL de QA revelam heranca administrativa (falha real)
STATUS: FAILED
AREA: architecture
DATE: 2026-10-25
RUN: none
JOB: r07-sec02-20261025 / Anthares Remote
COMMIT: chatgpt/sec02-neon-roles-qa-20261025
SUPERSEDES: 20261025-sec02-neon-principals-qa-lease.md

## Objetivo
Certificar em branch Neon isolada duas identidades LOGIN reais, uma por rede, com ALLOWED para a propria conta e DENIED para a outra.

## Protocolo
1. policy.py preflight (versao local f6fc9ca59a96e451) PASS; policy.py audit 218/0.
2. Branch QA exclusiva criada via Neon, sem tocar producao ou QA compartilhada.
3. Duas roles LOGIN com autenticacao por senha gerada pelo provedor; nenhum valor exibido ou registrado.
4. Duas schemas e tabelas com dados ficticios; GRANT USAGE e SELECT/UPDATE somente para a propria rede.
5. Consultas SQL efetivas via run_sql(role_name) comprovam current_user distintos e consultas proprias ALLOWED.
6. Consultas cruzadas inesperadamente retornaram dados; has_table_privilege indicou acesso tambem ao ledger copiado em QA.
7. Investigacao: ambas as roles membros INHERIT de neon_superuser; rolbypassrls=true, rolcreaterole=true, rolcreatedb=true.
8. Tentativa de reduzir privilegios apenas dessas duas roles QA: REVOKE neon_superuser FROM ... recusada com permission denied to revoke role neon_superuser. Recusa respeitada.
9. ROLLBACK: branch Neon QA exclusiva excluida pelo mecanismo autorizado; verificação list_branches(search, include_deleted=true) retornou lista vazia.

## Evidencia decisiva
- Principal Threads: propria tabela ALLOWED; tabela Instagram ALLOWED (falha).
- Principal Instagram: propria tabela ALLOWED; tabela Threads ALLOWED (falha).
- Ambos tinham privilege SELECT em public.cortes_publications, na copia QA. Nenhum dado dessa tabela foi efetivamente lido ou escrito.
- ACLs dos objetos sintéticos eram restritas; vazamento por elevacao administrativa herdada automaticamente do provedor.
- Nenhuma publicacao, token social, segredo BWS, workflow produtivo, fila, trigger, RLS ou banco de producao alterado.

## Consequencia
SEC-02 permanece PARCIAL. O mecanismo Neon create_postgres_role observado neste teste nao gera credenciais de minimo privilegio; nao repetir ate alteracao causal da concessao de neon_superuser pelo provedor. Recusa explicita de revogacao nao autoriza contorno por outro cliente. GitHub environment TikTok foi recusado em rodada historica, sem nova tentativa. Testes offline de secrets nao substituem prova IAM real.
