# Lease — campos e ativação do conto beta na mesma linha
STATUS: RUNNING
AREA: wordpress-beta-config-ui
DATE: 2026-10-31
JOB: chatgpt-20261031-beta-config-three-column
OWNER: ChatGPT GPT-6
COMMIT: d7ca261da039e53310317cf6719341709b4f6fa7
SUPERSEDES: test-hub/findings/20261031-beta-config-ui-production-proven-gpt6.md

EXCLUSIVE_SCOPE: `UniversoAnthares/anthares-wordpress` arquivo único `anthares-pix-sales/includes/65-leitura-beta.php`; HTML/CSS de `anthares_beta_render_config_contos`. Expiração 30 minutos.
USER_REQUEST: rótulo 'Quantas vagas?', descrição 'Quantos leitores poderão ler simultaneamente?', e ativação 'Disponibilizar este conto' na terceira coluna da mesma linha que vagas e Runas; botão de salvar abaixo.
BASELINE_PROVEN: branch GitHub main e blob lidos, página real fotografada. Design responsivo 3 colunas em desktop, empilha em largura estreita.
SAFETY: preservar nonce, names de inputs, backend, reserva financeira e ofertas; sem postagem nem transações em QA; testes PHP lint e QA externos Hostinger sem arquivos no computador, commits skip ci para não acionar runner Windows.
SUCCESS_SIGNAL: PHP lint/QA, HTML real com labels, CSS 3 colunas, checksum produção igual GitHub; nenhum Runas alterado.
FAILURE_SIGNAL: divergência live/main, falha lint/QA, quebra de checkbox ou layout.
