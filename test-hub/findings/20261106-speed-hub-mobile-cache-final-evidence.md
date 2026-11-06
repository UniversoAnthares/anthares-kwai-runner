# Anthares Speed Hub — evidências de produção
STATUS: PARTIAL
AREA: wordpress-performance
DATE: 2026-11-06
OWNER: ChatGPT
RUN: Hostinger live SSH, WordPress CLI, Chrome CDP mobile
SUPERSEDES: none

## Implantação e testes
- Hostinger 36-rankings.php: blob 61e0e33593a56c965ddd1c6514730290a75405fa; backup privado, atualização atômica e PHP 8.3 syntax PASS.
- Reconciliado o layout mobile mais recente da Hostinger com a otimização GitHub sem sobrescrever a interface.
- WP CLI: SNAPSHOT_CACHED=1, SNAPSHOT_EQUAL=1, SNAPSHOT_COUNT=16, MOBILE_CSS_HOOK=1.
- Invalidação por versão: CACHE_INVALIDATED=1, REBUILD_MATCHES=1, REBUILT_CACHE_PRESENT=1, RANK_COUNT=16.
- Chrome CDP Android 390x844: Home, /conto/um-dia-triste/ e /melhores-autores/ com readyState=complete, innerWidth=390, scrollWidth=390, sem overflow. Processo temporário próprio encerrado.
- Painel WP CLI admin: PANEL_FUNCTION=1, PANEL_RENDER_BYTES=1693, PANEL_METRIC_ROWS=13, SNAPSHOT_DB_VERSION=4.
- Scripts antes/depois: Home 79/28, conto 83/32, Melhores Autores 78/27. Checkout/Minha Conta mantêm scripts específicos.
- CSS/JS CDN: MISS -> HIT; HTML das páginas analisadas: DYNAMIC.

## Limite técnico aberto
- Cache HTML compartilhado da CDN segue deliberadamente desativado: HTML público inclui cookies e nonces de visitante/assistente, WooCommerce, formulários e outros componentes.
- Sem plugin ativo LiteSpeed Cache ou arquitetura de ESI/hole-punch validada; ativação exigirá tratamento abrangente de identidade e testes de isolamento.
- Teste móvel usa Chrome com emulação de viewport, sem aferição de LCP/CLS em aparelho físico.

## Código
- https://github.com/UniversoAnthares/anthares-wordpress/commit/3e8a729efef92192d0e29a70469630e6ba80d9a3