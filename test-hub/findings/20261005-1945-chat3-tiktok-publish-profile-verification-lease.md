# CHAT 3 lease — TikTok post-profile verification
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: d188c51a6f989136d72eeb85754b7b15c13e5248
SUPERSEDES: test-hub/findings/20261005-1944-tiktok-publish-confirmation-evidence-proven.md
LEASE_OWNER: CHAT 3 — TikTok produção/sessão/publicação real/escala
LEASE_START: 2026-10-05T19:45:36-04:00
LEASE_EXPIRES: 2026-10-05T20:10:36-04:00

BASELINE_PROVEN: tiktok_worker.inventory_profile_videos() é read-only, valida autenticação/identidade e coleta IDs/URLs do perfil com fallback de hidratação/API/DOM; o publisher já grava evidence somente depois de confirmação inequívoca de UI; o caller central agora aceita remote_id real ou confirmation_evidence explícita.
FAILED_AVOIDED: confirmação por clique/UI isolada não será tratada como prova de post no perfil; nenhuma publicação real será disparada enquanto tiktok-session permanecer bloqueada; não criar retry automático em estado ambíguo; não tocar em Cloudflare.
SUCCESS_SIGNAL: publisher captura inventário do perfil imediatamente antes do upload, confirma pela UI, captura inventário pós-publicação, identifica exatamente um novo vídeo e grava seu ID/URL como remote_id/remote_url com confirmação profile_new_post; ausência ou ambiguidade mantém falha/UNCERTAIN.
FAILURE_SIGNAL: publisher aceitar zero ou múltiplos candidatos novos como confirmação; inventário ignorar identidade; código permitir completar sem prova pós-publicação quando remote_id não estiver disponível.
TEST_VALIDITY: implementação e testes estáticos/unitários sobre comparação de inventários; nenhum canário real enquanto sessão não estiver PROVEN. A integração real será validada somente depois do desbloqueio de sessão.

## Objetivo
Acrescentar verificação pós-publicação independente usando o perfil TikTok já autenticado, produzindo remote_id real quando um novo post inequívoco aparecer.
