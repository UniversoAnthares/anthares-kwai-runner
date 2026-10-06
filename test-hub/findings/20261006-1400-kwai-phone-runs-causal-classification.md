# Kwai semantic Phone runs — causal classification
STATUS: SUPERSEDED
AREA: kwai-login
DATE: 2026-10-06
RUN: 37470175992; 37470224439; 37470232263
JOB: 112291308263; 112291473884; 112291500235
COMMIT: superseded by 63e15ac3ab3a8c1ca4fb7119a0ef030b7f86bfd7
SUPERSEDES: 20261006-1330 semantic Phone experiments

## Objetivo
Classificar os três experimentos Phone encerrados antes de qualquer nova repetição.

## Baseline
LOGIN_SURFACE_REACHED já PROVEN.

## Resultado
Os três runs convergem causalmente: o nó semântico Phone é com.kwai.video.basis:id/login_platform_expand_text, text='or use Facebook | Phone'. A ação leva a Chrome FirstRunActivity; a superfície observada depois pertence ao Chrome FRE. PHONE_EDITABLE_FIELDS=0 e KWAI_STUDIO_15_OBSERVATIONS_EXHAUSTED não provam ausência do fluxo de autenticação; provam que o harness antigo permaneceu observando a camada errada depois da transição web.

## Evidência decisiva
37470232263 registra PHONE_PATH completo, PHONE_ACTION_TARGET e topResumedActivity=com.android.chrome/...FirstRunActivity. 37470175992 e 37470224439 reproduzem a mesma transição.

## Consequência
Não repetir tap/ancestor/coordinate/deeplink para Phone. O único experimento corrente autorizado é 37470899378, commit 63e15ac3ab, que incorpora o Profile resource-id atualizado. Qualquer próximo passo deve partir do resultado desse run e tratar Chrome/web auth explicitamente.
