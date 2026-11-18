# Studio — correção do aviso de lixeira e QA ampliado
STATUS: PROVEN
AREA: anthares-studio/parity/qa
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-parity-20261118
COMMIT: 3731941ee13bcfd006defe35e371b854bd8d1389
PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/326
SUPERSEDES: test-hub/findings/20261118-studio-parity-regression-qa-proven.md

## Nova falha detectada
anst_trash_cleanup_enabled=0 na Hostinger, enquanto o texto da interface informava exclusão automática após sete dias e mostrava data definitiva. Código ajustado na branch para ler booleano real entregue pelo PHP e condicionar mensagem/data.

## Evidência de QA
- 92/92 testes Python PASS em checkout Hostinger isolado.
- PHP 8.3 lint PASS.
- JavaScript validado pelo parser V8: PASS.
- Manifesto QA 676/676 PASS e orquestrador PASS.
- Checkout temporário removido.
- A correspondência do banco após restauração realizada por outro executor é 71/71, com zero divergências em status, título, autor e conteúdo.
- A divergência de revisão de projeto é remapeamento correto de capítulo: origem 19547 para destino 21454.

## Continuidade
Novas alterações no JS de produção às 12:56Z foram detectadas enquanto este trabalho ocorria. Sem sobrescrita de arquivo concorrente; implementar reconciliação de hash antes de qualquer promoção. Permanecem pendentes E2E autenticado, autorizações de piloto e QA visual no projeto. O acesso do conector de abas foi limitado pela permissão do host; manter sem contorno.