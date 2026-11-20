# Lease de implantação: Anthares Studio — item 1

DATA: 2026-11-20
OWNER: ChatGPT
STATUS: CLOSED_DEPLOYED_VERIFIED
ESCOPO: somente 3 arquivos em /wp-content/plugins/anthares-studio:
- assets/studio-g7-comments.js
- assets/studio-g6-navigation.css
- includes/domain/class-anst-g7-comments.php
SOURCE: ZIP validado no site, anthares-studio-item1-comentarios-20261120.zip, SHA256=7796efad7e9e3590bb2c2d977de1bc3b6bdc548ebb401e5fbe1ae476adc20fbc
PR: UniversoAnthares/anthares-wordpress#385, merged.
PRECONDICOES: conferir SHA e paths, fazer backup privado, evitar alterações concorrentes, restaurar backup caso lint/REST falhe.
EVIDENCIAS ANTERIORES: 130 testes unitarios Python, 22 REST transacionais, QA UI mobile e desktop.
DADOS: proibido tocar dados reais e versão legada /estudio; arquivos de teste e backup somente no Hostinger, fora do public_html.
RESTRICAO: qualquer recusa de segurança interrompe a implantação e não autoriza trocar de canal.

CLOSED_UTC: 2026-11-20T15:48:00Z
RESULT: deployed exactly three checked SHA256 files in production, after private backup. PHP syntax PASS, 51 Python tests PASS, both public JS/CSS served match local hashes, /studio and /estudio HTTP200, plugin active, 22 original projects intact.
REPORT: test-hub/findings/20261120-studio-item1-hostinger-deployed.md
