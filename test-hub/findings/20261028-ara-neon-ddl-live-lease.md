# ARA/Neon — remover DDL de requisições em produção
STATUS: RUNNING
AREA: queue / ara-neon-cost / vercel-ara-primary
DATE: 2026-10-28
OWNER: ChatGPT GPT-6 (item fixo 3)
BASELINE_PROVEN: Vercel Production READY dpl_k7VUu3p222MnC4rNeLAZp6q84zFf em e8a9609ce6e6b2948082ba02a490b87ee0641ced. entry blob 94cc2c861700c0204bf50b6eb7c1f0b61a362587 e router blob ad7b212d9505ca9b26d9e67fd47d776fc5cfeff4. Neon tabela ara_oauth_consumed, constraint ara_reserve_jobs_status_check e indice ara_reserve_jobs_dedupe presentes. Governance 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1. GitLab peer inspecionado (entry idem, router diverge por integracao Vercel Hostinger).
FAILED_AVOIDED: PR #1807 contem patch isolado, ainda nao publicado. Preservar wake notifier, OAuth consume, SAFE_RETRY, leaseNext, reap, result, schema preexistente e controles de producao item 5. Nao modificar schema, segredos ou agente.
SUCCESS_SIGNAL: remover ensureCompatibility e DDL de entrada HTTP; manter ensureSchema apenas no fluxo OAuth consumido; sintaxe/CI PASS, deployment production READY no commit reconciliado, HTTP health e MCP ARA efetivos, ausencia de DDL em cold start, idempotencia/constraint presentes.
FAILURE_SIGNAL: HEAD/deployment alterado por concorrencia, build falha, autenticacao/filas regredidas, tabela/indices ausentes.
TEST_VALIDITY: rota de health e ARA reais, nao confundir READY com validacao; exigir pre/post cotejo exato de code blob e verificacao de producao. Testes minimos proporcionais.
SUPERSEDES: none
LEASE: maximo 30 minutos a partir de criacao, apenas nesta branch e deployment ARA, encerrar com finding append-only.
