# Lease: consertar acesso aos assets públicos de /studio
STATUS: RUNNING
START_UTC: 2026-11-16T20:45:00Z
EXPIRES_UTC: 2026-11-16T21:20:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
AREA: studio-static-assets-production-permission-repair
REASON: diretórios plugin anthares-studio / assets são 700; JavaScript e CSS 600. HTTP GET /wp-content/plugins/anthares-studio/assets/estudio.js retorna 404. A página privada contém [anthares_studio]; shortcode e plugin ativos; 404 bloqueia renderização JS.
ALLOWED: corrigir para 755 apenas diretórios public_html/wp-content/plugins/anthares-studio, assets e assets/vendor; 644 apenas arquivos JS/CSS necessários (estudio.js, estudio.css, estudio-dark.css, vendor/quill-2.0.3.js, vendor/quill-2.0.3.snow.css). Conservar PHP 600, arquivo .bak privado e dados/campos/status.
FORBIDDEN: tocar anthares-estudio, alterar código, conteúdo/posts, flags de escrita, visibilidade privada, login, plugins de segurança, cache global.
TEST: HTTP status/assets 200 e content-type adequado, texto de JS, PHP syntax and original SHA unchanged. rollback das permissões caso falha.
GOVERNANCE: sha 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1.
