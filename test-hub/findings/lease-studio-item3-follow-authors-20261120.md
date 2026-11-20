# Lease Anthares Studio — item 3 Seguir autores

STATUS: CLOSED_DEPLOYED_VERIFIED
OWNER: ChatGPT
DATE: 2026-11-20
SOURCE: `site-anthares.docx`: 'cada usuário tem que ter um botão de seguir, pra quando esses autores publicarem aparecer na home de quem quer acompanhar'; item 3 da lista renumerada: seguir autores e publicações.
SCOPE: `anthares-wordpress` branch `feat/studio-follow-authors-item3-20261120`; módulo PHP/JS/CSS de following, integração mínima `anthares-customify/author.php`, `anthares-studio/anthares-estudio.php`, interface `studio-g7-public-reader` e testes. Visualizar publicações recentes em página pessoal do Studio; não modificar feed de home global (item 13 descartado).
EXCLUDE: item 4 notificações; nenhuma comunicação enviada, sem contas reais editadas, sem compra e sem publicações novas públicas. QA reversível em MySQL transaction; backup privado antes de instalar.
EXIT: seguir/deixar de seguir, lista privada, feed de publicações públicas, anti-auto-follow, teste de anonimato, proteção de dados e retirada de publicação, operação em WordPress atual e registro de evidências.

CLOSED_UTC: 2026-11-20T19:42:00Z
RESULT: item 3 implemented, merged to WordPress main via PRs #387 #388 #389; 7/7 plugin runtime files installed and SHA256-verified, theme left untouched because of source drift. 161 Python tests, 31 WP REST transaction rollback tests, QA manifest 723 PASS, production plugin 51 tests PASS, anonymous 401, profile widget real-browser PASS. Details: test-hub/findings/20261120-studio-item3-follow-authors-deployed.md.
