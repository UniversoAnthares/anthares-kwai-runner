# ARA Neon — DDL de entrada HTTP eliminado em produção
STATUS: PROVEN
AREA: queue / ara-neon-cost / vercel-ara-primary
DATE: 2026-10-28
OWNER: ChatGPT GPT-6, item fixo 3
RUN: Vercel production dpl_34YfhFrAn84AxPvgW3XRrrhu6EJd
JOB: health GET https://anthares-remote-primary.vercel.app/health
COMMIT: 780290e39bf6dc56ee1af7503b37da9a5e219074
SUPERSEDES: test-hub/findings/20261028-ara-neon-ddl-live-lease.md

## Resultado
Patch reconciliado sobre a producao anterior e8a9609ce6e6b2948082ba02a490b87ee0641ced (preserva Hostinger item 5). router-entry.mjs blob c38544ca1800f7714e71e28c1a3ab7868a2ef4bb: excluido Pool/ensureCompatibility e ALTER TABLE DROP/ADD CHECK de toda requisicao. router.mjs blob 17d4ffdef1af87ac7310c0f20aecbc26eb5d99c0: excluido await ensureSchema no handler; mantido em consume de OAuth para compatibilidade. SAFE_RETRY, reap, leaseNext, resultados, controles MCP, OAuth e wake notifier sem modificacoes funcionais.

## Prova
Vercel gitSource production READY e alias anthares-remote-primary.vercel.app no SHA exato, build sem erro. GET /health externo apos deploy devolveu ok=true, state=neon, oauth=true, mcp=true, device_connected=true. Neon catalogo read-only confirma ara_oauth_consumed, ara_reserve_jobs_status_check e ara_reserve_jobs_dedupe existentes. Anthares Remote session_status conectada com 0 uncertain no momento consultado. Integracao Anthares Remote para comando de smoke abortou sem retorno final; essa verificacao isolada nao foi classificada como sucesso. Estado de idempotencia e lease preservado estaticamente; CU-h real reservado para item 7.

## Rollback
Vercel deployment anterior dpl_k7VUu3p222MnC4rNeLAZp6q84zFf (SHA e8a9609...). Sem migracao de banco, sem alteracao de secrets, agente ou filas Git.
