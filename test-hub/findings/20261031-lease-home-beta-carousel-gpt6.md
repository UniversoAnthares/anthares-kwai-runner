# Lease — microseção de ofertas beta, carrossel e bloco triplo
STATUS: RUNNING
AREA: wordpress-home-beta-opportunities
DATE: 2026-10-31
RUN: none
JOB: chatgpt-20261031-beta-three-slots
COMMIT: d63486f9d96a3685c4e4def87b718925f10be34c
SUPERSEDES: test-hub/findings/20261031-home-beta-opportunities-production-proven-gpt6.md

## Escopo exclusivo
Owner ChatGPT GPT-6, expira 30 minutos após criação. Arquivos do repo `UniversoAnthares/anthares-wordpress`: template e CSS da seção `leituras-beta-disponiveis`, dimensões da seção no layout, e rota read-only do próprio conto em `anthares-pix-sales/includes/65-leitura-beta.php`. Exclusão de widgets 'Gerenciar oferta' e aviso relacionado, exibir somente ofertas ativas financiadas. Visibilidade de toda oferta, inclusive a própria, para papel exato `anthares`; outros papéis mantêm regras. Container de 3 posições internas, primeira ocupada, outras reservadas para definição futura, carrossel de 1 item com seta direita. Preserve outros layouts e lógica de Runas.
BASELINE_PROVEN: checkout de role anthares e render em Hostinger; checkout PHP 8.3 disponível. Render com filtros anteriores excluía self e inseria uma oferta pessoal não ativada. Extensão da Home usa grid de 4 quartos; precisa de container interno triplo independente.
SUCCESS_SIGNAL: unit QA e PHP lint, template mostra próprio item somente se oferta ativa e financiada, indicação de vagas e Runas em super destaque, clicabilidade do título, carrossel de 1 por vez, próprio texto acessível read-only, bytewise production match.
FAILURE_SIGNAL: exposição pública não autorizada, self avança para pagamento, SQL falha, erro de layout/JS, PHP sintaxe, divergência em production ou transação financeira.
TEST_VALIDITY: testes SQL/read-only, render WP-CLI, PHP lint, QA manifests, inspeção browser, sem criação de ofertas e sem saldos afetados, sem arquivos no PC.
