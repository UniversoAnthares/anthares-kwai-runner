# Lease — Anthares Studio, item 4 (notificações de autores seguidos)

STATUS: ACTIVE
START: 2026-11-20
OWNER: ChatGPT
SOURCE: `site-anthares.docx`: botão de seguir dá notificações no próprio site, sem email. Lista de 22 itens renumerada, item 4.
REPO: `UniversoAnthares/anthares-wordpress`, branch `feat/studio-follow-notifications-item4-20261120`.
SCOPE: plugin `anthares-studio/includes/domain/class-anst-g7-follow-notifications.php`, `class-anst-g7-publishing.php`, `anthares-estudio.php`, testes. Usar sino, catálogo, preferências e fonte de seguidores existentes. Eventos novos capítulos públicos G7 e posts/contos publicados; deduplicação, segurança, privacidade e múltiplos usuários. Sem emails e sem alteração da home.
GATES: backups privados, comparar SHA ativo vs main, lint PHP, tests, transactional E2E com ROLLBACK, manifesto, verificação sem alterar dados reais, URLs e segurança. Respeitar autorizações operacionais e isolamento do tema ativo.
