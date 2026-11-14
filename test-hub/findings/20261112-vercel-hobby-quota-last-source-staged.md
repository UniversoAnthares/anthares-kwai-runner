# Vercel Hobby — quota bloqueada demovida para a última posição (código preparado)
STATUS: PARTIAL
AREA: vercel/quota-routing
DATE: 2026-11-12
OWNER: chatgpt-gpt6-20261112-vercel-quota
SUPERSEDES: test-hub/findings/lease-20261112-vercel-hobby-quota-demotion-gpt6.md
LEASE: CLOSED
SOURCE_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2462
BASE_SHA: d17d8b6dbfb417b2f01039b1156d8cd41164fb7d
PROPOSED_BRANCH: fix/vercel-hobby-quota-tail-20261112-gpt6

## Observação direta
Painel Vercel Hobby autenticado pelo perfil AntharesVercel em 2026-11-12: Deployments Paused desde 2026-10-29 por limite Fluid Active CPU e término indicado 2026-11-28. API de cobrança devolveu costs_not_found; portanto não inferir valores de CPU ou disponibilidade de funções a partir de build count. Test Hub AOI #8 registrou Vercel HTTP 402 DEPLOYMENT_DISABLED em 2026-11-04.

## Alterações de código nesta branch
- ci-hub/quota-status.json: registra o quota_scope de CPU Vercel, marca BLOCKED_QUOTA e elegibilidade=false até prova atual.
- ci-hub/provider-status.json: reconciliado com a quota observada, Vercel compute elegível=false e Neon/Cloudflare preservados.
- ci-hub/executor-routing.json: ordenação para novos jobs GitLab private queue > GitHub private queue > Vercel; Vercel última e inelegível. O campo current_selected_backend histórico fica explicitamente STALE e NÃO é promovido automaticamente a outro executor.
- tools/ci_quota_cancel_first.py: demote_blocked_scopes reordena sem perder ordem das reservas saudáveis. cancel_first exclui aliases com mesmo quota_scope e escopos bloqueados da seleção, mesmo que um registro de elegibilidade esteja obsoleto. Preserva cancelamento terminal, reconciliação NOT_APPLIED e idempotência pré-existentes.
- tests/test_ci_quota_cancel_first.py: casos de prioridade saudável, aliases de quota compartilhada e ausência de reserva.

## Provas e limites
Validação estática: ambos os arquivos JSON foram decodificados com sucesso e relidos do branch; a prioridade resultante coloca Vercel ao final e remote_backend_eligible=false. Arquivos Python relidos com SHA novo. Validação dirigida em 2026-11-12: o código Python exato da branch passou AST parse e cinco casos funcionais em memória (5 PASS, 0 falhas), com seleção simulada da reserva Neon e zero despachos externos/arquivos persistidos. O job hospedado CI completo segue UNVERIFIED e não foi disparado. Nenhuma ação em produtor, mídia, contas, banco, credenciais, workflows ativos, DNS, planos ou pagamentos.
Contingência conhecida: Anthares Remote utiliza Cloudflare WebSocket e ledger Neon compartilhado; recibos de quota CI possuem controlador Neon/OIDC com 19 recibos históricos verificados. Essa cobertura tem limites de escopo. Funções Vercel genéricas exigem adaptador equivalente com quota independente e lease/fencing antes de cutover. Não afirmar substituição universal.

## Critério terminal pendente
PR integrada após QA dirigido; configuração efetivamente carregada pelo despachante; prova de seleção após uma falha real de quota sem trabalho duplicado. Não induzir falha nem publicar mídia para testar. Preservar Vercel em último lugar até restabelecimento e comprovação de cota, inclusive após 2026-11-28.
