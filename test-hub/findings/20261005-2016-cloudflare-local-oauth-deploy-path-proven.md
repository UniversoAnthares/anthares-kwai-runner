# Caminho de deploy Cloudflare via OAuth autorizado no PC
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: readonly-wrangler-whoami
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2008-cloudflare-production-stale-local-fallback.md
FAILED_AVOIDED: não repetir GitHub deploy com CLOUDFLARE_API_TOKEN ausente; não usar PC como executor/fallback de produção; não expor token OAuth.
SUCCESS_SIGNAL: wrangler whoami no computador autorizado confirma sessão Cloudflare válida e permissão workers write.
FAILURE_SIGNAL: sessão ausente/expirada ou sem permissão de deploy.
TEST_VALIDITY: comando somente-leitura; nenhum deploy, alteração de Worker, fila, sessão ou estado foi realizado.

## Objetivo
Descobrir uma rota causal para implantar o snapshot endurecido sem depender do secret CLOUDFLARE_API_TOKEN ausente no runner GitHub.

## Resultado
PROVEN: `npx --yes wrangler@4.43.0 whoami` concluiu com exit code 0 no computador autorizado. A sessão OAuth existente possui acesso à conta Cloudflare do projeto e escopos de escrita para Workers/KV. Nenhum valor de token foi lido ou registrado.

## Evidência decisiva
Wrangler retornou `You are logged in with an OAuth Token` e listou `workers (write)`, `workers_kv (write)`, `workers_scripts (write)` e demais permissões relacionadas.

## Consequência
Após o lease ativo de `cloudflare-control` encerrar e após reler HEAD/hub, o snapshot endurecido pode ser implantado com Wrangler a partir do computador autorizado como console de deploy. Isto não reintroduz PC como runtime, executor ou fallback: após o deploy, Worker/Durable Object continuam operando na Cloudflare sem depender do computador. Antes do deploy, comparar o snapshot local/HEAD e preservar KV/Durable Object/migrations.