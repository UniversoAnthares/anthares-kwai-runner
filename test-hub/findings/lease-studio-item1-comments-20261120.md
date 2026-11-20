# Lease — Anthares Studio pendência ativa 1 (comentários por parágrafo)

OWNER: ChatGPT
STATUS: CLOSED_CODE_MERGED_FTP_PENDING
START: 2026-11-20
SCOPE: `anthares-wordpress/anthares-studio/assets/studio-g7-comments.js`, `assets/studio-g6-navigation.css`, `includes/domain/class-anst-g7-comments.php`, testes relacionados. Branch `feat/studio-paragraph-comments-20261120`.
OBJECTIVE: marcador lateral por parágrafo; discussão encadeada e moderação de autor; vínculo de edição imutável; validação de âncora/respostas. Reaproveitar WP Comments e evitar duplicação de dados.
EXCLUSIONS: item 6 (comentários no perfil), outros itens 2-22, publicação comercial e modificação de conteúdo real. Preservar `/estudio/` e UX existente.
GATES: backups antes de deploy, lint PHP/JS, testes unitários/REST, QA autenticado se edição real liberada, no changes to user content. Proibir criação de contas sem autorização.

CLOSED_UTC: 2026-11-20T15:36:00Z
CODE: PR 385 merged to WordPress main, commit 34f73c11b0cddf45fb8428bc078b1b60332e4279. Testes 130/130 Python, 22/22 REST transactional, PHP/JS lint, 714/714 QA manifest. Browser synthetic mobile 390/768/1440 px, no overflow.
PRODUCTION: still old plugin files as of 15:34Z. ZIP supplied for FTP; post-deploy E2E pending. Report: test-hub/findings/20261120-studio-item1-comments.md
