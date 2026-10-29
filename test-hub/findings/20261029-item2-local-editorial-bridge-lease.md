# Item 2 — extensão do lease após identificar bloqueio real no Forgejo
STATUS: RUNNING
AREA: tiktok/forgejo-producer-editorial-local-bridge
DATE: 2026-10-29 UTC
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40880594122
JOB: 123470743304
COMMIT: ac092439054a00942f95ed957bfab22fc1318e22
SUPERSEDES: 20261029-item2-producer-contract-lease.md
LEASE: ampliar exclusivamente para UniversoAnthares/anthares-clipper/{cortes_tiktok_enqueue.py,cortes_editorial_transport.py,cortes_forgejo_wp_bridge.php,tests/test_cortes_tiktok_enqueue.py}, dono ChatGPT item2; concluir com PR, CI green e readback.

CAUSA: Forgejo WordPress producer tem FORGEJO_REPOSITORY e usa local_wp_request('state'), mas em eligible usa cortes_editorial_transport.editorial_for_clip que depende de WP_SITE_URL + wp_get HTTP e não possui caminho local; sem WP_SITE_URL o Forgejo falha em obter metadados canônicos dos attachments, tornando candidatos=0 silenciosamente. Preflight run #238 de identidade não prova enqueue. O teste de contrato #40880594122 tem 4 failures e 1 error com fixtures inline titulo antigas sem attachment canonical. Corrigir rota local de apenas mídia por WP REST via WP-CLI, mantendo validações de media id, WP principal edit_posts, somente campos title/description/caption/alt_text, nenhum segredo, e testes de canonical metadata e isolamento de edição.
SCOPE: não tocar credenciais, TikTok publisher, flags Actions, quotas, Neon, estado uncertain ou outras tarefas. Preflight/contratos sem publicação, seguido de implantação GitHub→Forgejo pela sincronização já existente; promoção produtiva ainda requer admin approval, exclusão mútua e recibo Neon.
DONE: CI do contrato verde, liberação do lease; sem alegação de handoff concluído sem prova.