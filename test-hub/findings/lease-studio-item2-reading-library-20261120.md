# Lease — Item 2: Favoritos e listas de leitura do Anthares Studio

STATUS: ACTIVE
OWNER: ChatGPT
START: 2026-11-20
REQUIREMENT: briefing `site-anthares.docx`, lista renumerada item 2: favorito, salvar, organizar em listas e continuar capítulo entre sessões, preservando privacidade.
SCOPE: `anthares-wordpress/anthares-studio`: novo módulo PHP `includes/domain/class-anst-g7-library.php`, JS `assets/studio-g7-library.js`, CSS `assets/studio-g6-navigation.css`, bootstrap `anthares-estudio.php`, testes em `tests`. Branch `feat/studio-reading-library-item2-20261120`.
EXCLUSIONS: lista 3 (seguir autores), lista 4 (avisos), pagamento, membros sem permissão, conta real, publicações, dados de outros usuários. Preservar `estudio/` e navegação de cinco entradas.
GATES: lint, 51+ tests, REST E2E transactional with rollback, authenticated browser when available, predeploy backups and postdeploy SHA. Coordinate ownership before writes. Never change existing public content or create external emails.
