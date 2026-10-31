# Home beta: contêiner triplo e paginação — produção validada
STATUS: PARTIAL
AREA: wordpress-home-beta-opportunities + wordpress-beta-config-ui
DATE: 2026-10-31
JOB: chatgpt-20261031-beta-container-pagination
COMMIT: 50d962c9a6fb9fee79eedb1b8ee09eacc1c5b43f
SUPERSEDES: test-hub/findings/20261031-lease-home-beta-container-pagination-gpt6.md

## Publicado e validado
- PR WordPress #219, merge `50d962c9a6fb9fee79eedb1b8ee09eacc1c5b43f`.
- Home `Ler e participar`: contêiner externo com borda/fundo, 3 posições internas com borda, 2 vazias; vagas como coluna intermediária junto ao topo do autor; Runas como valor destacado à direita.
- Configuração: o título do tema Customify `#page-titlebar` fica oculto apenas quando `.anth-beta-config` está na página; menos espaço acima do botão; texto de ativação alinhado à direita; paginação server-side de dez contos por página via `WP_Query`, navegação preserva `configurar=contos`.
- Hostinger: PHP 8.3 lint PASS nos 2 PHP; QA manifest 601/601 PASS; QA orchestrator PASS. Os 3 arquivos publicados comparados byte a byte ao GitHub main `MATCH_NEW`, backup externo privado. CSS via HTTP 200.
- WP-CLI runtime: OUTER_CONTAINER PASS; EMPTY_POSITIONS 2; RUNA_VALUE PASS; TITLEBAR_RULE PASS; PAGINATION_STYLE PASS; FORM_SAVE PASS; PAGINATION_COUNT 2 (somente 2 contos no papel testado, logo barra de navegação oculta). Testes não criaram ofertas ou transferiram Runas.
- Clones e temporários externos da tarefa removidos. Nenhum arquivo no PC.

## Dependência visual pendente
O arquivo oficial do símbolo monetário das Runas ainda não foi encontrado no repositório nem no WordPress (busca assets por nomes relacionados). Em vez de inventar um desenho, o template aceita `apply_filters('anthares_runa_simbolo_url','')`; uma URL oficial poderá renderizar `img.anth-beta-discovery__runa-icon` ao lado direito do número. Até essa vinculação, mantém o texto 'Runas'. Requer publicação/identificação do asset oficial e integração pelo filtro.

## Limites
Navegação paginada entre páginas 2+ depende de conta com mais de dez contos beta; contrato e consulta implementados, não foram criados contos sintéticos em produção. Não houve homologação visual interativa com screenshot de navegador autenticado, apenas QA de markup+CSS+PHP/WordPress.
Lease encerrado sem substituir código concorrente.
