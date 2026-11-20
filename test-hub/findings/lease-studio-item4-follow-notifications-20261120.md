# Lease — Anthares Studio, item 4 (notificações de autores seguidos)

STATUS: CLOSED_DEPLOYED_VERIFIED
START: 2026-11-20
OWNER: ChatGPT
SOURCE: `site-anthares.docx`: botão de seguir dá notificações no próprio site, sem email. Lista de 22 itens renumerada, item 4.
REPO: `UniversoAnthares/anthares-wordpress`, branch `feat/studio-follow-notifications-item4-20261120`.
SCOPE: plugin `anthares-studio/includes/domain/class-anst-g7-follow-notifications.php`, `class-anst-g7-publishing.php`, `anthares-estudio.php`, testes. Usar sino, catálogo, preferências e fonte de seguidores existentes. Eventos novos capítulos públicos G7 e posts/contos publicados; deduplicação, segurança, privacidade e múltiplos usuários. Sem emails e sem alteração da home.
GATES: backups privados, comparar SHA ativo vs main, lint PHP, tests, transactional E2E com ROLLBACK, manifesto, verificação sem alterar dados reais, URLs e segurança. Respeitar autorizações operacionais e isolamento do tema ativo.

CLOSED_UTC: 2026-11-20T22:47:00Z
RESULT: WordPress PR #390 merged, three plugin files installed and hash-matched; two types registered and enabled in global and user settings; 175 Python PASS, 33 WP REST transaction PASS with ROLLBACK, 726 QA files exactly once, production plugin 51 PASS, /studio/ /estudio/ HTTP200, 22 original projects intact. Production backup outside public_html. Full report: test-hub/findings/20261120-studio-item4-follow-notifications-deployed.md.
