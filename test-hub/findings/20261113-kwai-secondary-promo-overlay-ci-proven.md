# Kwai secundária: fechamento estrito da promoção — CI aprovado
STATUS: PROVEN
AREA: kwai
DATE: 2026-11-13
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43526056033
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43526056033/job/132231975660
COMMIT: 58e86b3eb0854efe7d32df28dffa3512549d012a
SUPERSEDES: 20261113-kwai-secondary-promotion-popup-running.md

## Evidência
O XML salvo pelo executor secundário em 13/11 às 19:12 continha 123 nós e a aba do perfil. O XML seguinte às 19:13 continha 6 nós, incluindo apenas uma promoção opcional com view_content, colored_button_bg e close_button, este último clickable/enabled com bounds [905,532][977,604]. O erro missing:id_home_bottom_tab_me aconteceu enquanto esse popup ocultava a aba.
O código existente kwai-up/kwai_up.py já reconhecia o mesmo trio; tools/kwai_native_cortes.py foi atualizado para fechar somente o botão confirmado nessa combinação exata, apenas na conta secundária, e reabrir a inspeção do perfil.
CI 43526056033: Node pass 37 fail 0; Python KWAI_SECONDARY_EXACT_PROMO_DISMISS_PASS; KWAI_SECONDARY_PROMO_INVALID_NO_TAP_PASS; KWAI_UNKNOWN_PROMPT_FAIL_CLOSED_PASS; todos os testes legados passaram.

## Limites
Teste offline, sem ADB, sem publicação nem mudança da fila. Primária possui publicação STARTED em produção às 19:14:39, com prova pública pendente, portanto não reiniciar os daemons nem alterar o lease ou limpar ACK em trânsito. A secundária está em backoff legítimo de 1800 segundos por falha pré-publicação (possible=False); preservar. Implantar somente o módulo em disco quando a versão GitHub for revisada e o SHA da versão local for verificado. Registrar prova da próxima execução real antes de declarar publicação secundária restabelecida.
