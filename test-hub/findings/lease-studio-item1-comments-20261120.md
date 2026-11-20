# Lease — Anthares Studio pendência ativa 1 (comentários por parágrafo)

OWNER: ChatGPT
STATUS: ACTIVE
START: 2026-11-20
SCOPE: `anthares-wordpress/anthares-studio/assets/studio-g7-comments.js`, `assets/studio-g6-navigation.css`, `includes/domain/class-anst-g7-comments.php`, testes relacionados. Branch `feat/studio-paragraph-comments-20261120`.
OBJECTIVE: marcador lateral por parágrafo; discussão encadeada e moderação de autor; vínculo de edição imutável; validação de âncora/respostas. Reaproveitar WP Comments e evitar duplicação de dados.
EXCLUSIONS: item 6 (comentários no perfil), outros itens 2-22, publicação comercial e modificação de conteúdo real. Preservar `/estudio/` e UX existente.
GATES: backups antes de deploy, lint PHP/JS, testes unitários/REST, QA autenticado se edição real liberada, no changes to user content. Proibir criação de contas sem autorização.
