# Kwai secundária — seletor de Próximo após promoção corrigida
STATUS: RUNNING
AREA: kwai
DATE: 2026-11-13
RUN: none
JOB: none
COMMIT: 872305e73dbfe6b1be1a8107dffb821660081442
SUPERSEDES: 20261113-kwai-secondary-promo-overlay-ci-proven.md
OWNER: ChatGPT / Kwai native selector, path-scoped

## BASELINE_PROVEN
Tentativa secundária de 13/11/2026 às 19h43 ultrapassou fechamento do popup, validou SHA256 da mídia e MediaStore, mas falhou antes de publicar (possible=False) com missing:kwai.lite.video.basis:id/editor. Dumps com 65 nós antes/depois de duas tentativas de Próximo mostram com.kwai.video.ca_product:id/edit_next_button FrameLayout, clickable=true, enabled=true, bounds [555,2052][1029,2134]; o filho com.kwai.video.ca_product:id/next_button_normal tem texto Próximo, clickable=false, bounds [703,2052][880,2134]. Existe um botão Publicar separado à esquerda. O seletor RID_NEXT atual usa o filho não clicável e ignora o pai clicável. Distinguir claramente o controle antes do teste físico.

## FAILED_AVOIDED
Não tocar Android em paralelo com publicação primária, não clicar Publicar no editor, não reativar fila falha, não zerar backoff, não incluir autenticação e nenhuma mídia privada no teste.
## SUCCESS_SIGNAL
CI offline prova que RID_NEXT seleciona apenas o pai habilitado, clicável com filho semântico Próximo, rejeita botão Publicar e pai desabilitado, com regressões gerais aprovadas. Deploy em disco só após nenhum job em fase crítica e versão local validada. Nova publicação real secundária requer prova posterior no Neon/WordPress.
## FAILURE_SIGNAL
Escolha de Publicar no estágio de edição, seleção de nós não clicáveis, ou regressão no Kwai Lite.
TEST_VALIDITY: XML sintético sanitizado, zero toque em dispositivo, sem média, sem credencial.
