# CORTES — LinkedIn daily limit deployed on current Vercel production
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-20
RUN: https://vercel.com/lucasyahn-6808/anthares-remote-primary/2teWgnEzEorSNRSnZ6Ju2NrK4jtz
JOB: deployment dpl_2teWgnEzEorSNRSnZ6Ju2NrK4jtz
COMMIT: beb7ca06142aefe746759ed50747d247ca8eae82
SUPERSEDES: test-hub/findings/20261020-2052-lease-vercel-linkedin-prod-preserve-tiktok.md

## Objetivo
Instalar LinkedIn 20/dia no backend atual sem reverter a cadência TikTok do hotfix de produção.

## Evidências
Projeto Vercel anthares-remote-primary, produção anteriormente dpl_87aaMmBdwPMGcFnnRDyMVDhFnmT8 SHA 90c5f3175909b0ec8162ad31af7ee27ca72198c2. Nova branch isolada baseou-se exatamente nessa SHA, adicionando somente o bloqueio de quota transacional ao endpoint /api/cortes-queue, commit beb7ca06142aefe746759ed50747d247ca8eae82. Staging dpl_FiwdCt7hGKGrX8R86aD1xfDu8xEe READY e build compilado. Production dpl_2teWgnEzEorSNRSnZ6Ju2NrK4jtz READY confirmado via Vercel MCP. GET https://anthares-remote-primary.vercel.app/api/cortes-queue?action=health HTTP 200, ok true, backend vercel-neon, fencing true, dedupe true; GET /api/cortes-tiktok?action=health HTTP 200 ok true. Neon preservado, sem alteração de registros existentes.

## Escopo comprovado
Código do limite LinkedIn está em produção. Pinterest sem teto lógico já era comportamento do Neon. Publicação real nas duas redes permanece PENDING AUTH; não afirmar redes ativas. O executor social e as credenciais ainda não existem no runtime de produção. A branch de deploy mantém os patches TikTok ativos, enquanto GitHub main contém os adaptadores da PR269; unificação de branches deverá ser realizada sem apagar hotfixes.
