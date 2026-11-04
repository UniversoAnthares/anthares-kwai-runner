# WordPress Telegram — botão único discreto
STATUS: PARTIAL
AREA: wordpress-telegram
DATE: 2026-11-03
RUN: no live run
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/220
COMMIT: 326f24bc36a51fd07a02e71b2f863f31a93f9f6b
SUPERSEDES: test-hub/findings/20261103-wordpress-telegram-one-button-lease.md

## Resultado
Página Telegram do fórum e dos contos: estado inicial renderiza um único botão "Enviar para o canal no Telegram". Clique expande texto breve, campo, ações e controle de conta; segundo clique/Esc recolhe. PHP/JS/CSS alterados na PR #220, preservando o link anthares_topico_id e o preflight de saúde do relay.

## Evidência
Parser JavaScript + simulação click-click-Escape em código da branch PASS; atributos aria-expanded/aria-controls, hidden e CSS hidden!important PASS; php -l no bloco PHP modificado PASS. Não foi executado php -l do plugin completo, nem QA no WordPress real. Compara HEAD main antes da mutação e blob dos três arquivos; SHA de branch mantido. Status GitHub Vercel failure corresponde à conta de deploy bloqueada.

## Gate e responsabilidade
Checagem equivalente do inventário QA por tree recursiva e manifests mostra 605 arquivos auditáveis, 601 atribuídos e faltam quatro arquivos anthares-home: assets/css/dashboard/ler-e-participar-pagina.css, assets/css/dashboard/recem-grid.css, includes/anthares-ler-participar-pagina.php, includes/class-anthares-home-recem-grid.php. Não editar manifestos sem dono; coordenar outro agente responsável por anthares-home. Bloqueia merge/deploy. Site continua com a versão antiga. Lease encerrado. Retomar com novo lease e QA formal/implantação.
