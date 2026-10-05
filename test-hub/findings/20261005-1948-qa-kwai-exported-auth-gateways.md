# Exported Kwai auth/login gateways narrow next causal test
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388030409
JOB: 112026171392
COMMIT: d9a144b23fbca831e4b382aa710549b68d9af77a
SUPERSEDES: none

## Objetivo
Extrair do Manifest validado somente componentes login/auth realmente exported=true e reconciliar com o antigo TARGET_COUNT=0.

## Resultado
Há componentes exportados relevantes. TinyGoogleSSOActivity e TinyUserInfoActivity estão exported=true. Também estão exported=true OpenAuthActivity, KwaiAuthActivity e LivePartnerAuthActivity; os três últimos têm gateways/deeplinks declarados. Logo o antigo direct probe que produziu TARGET_COUNT=0 por filtragem de dumpsys não prova que todos os Tiny* sejam runtime-iniciáveis/inexistentes; pelo menos a declaração/exportação está comprovada no Manifest.

## Evidência decisiva
Manifest do run 37388030409:
- com.yxcorp.gifshow.tiny.login.activity.TinyGoogleSSOActivity exported=true
- com.yxcorp.gifshow.tiny.login.activity.TinyUserInfoActivity exported=true
- com.yxcorp.gifshow.oauth.activity.OpenAuthActivity exported=true, scheme=com.kwai.video
- com.yxcorp.gifshow.authorization.KwaiAuthActivity exported=true, VIEW/BROWSABLE, schemes ikwai/kwai/ikwaibulldog host=authorization
- com.yxcorp.gifshow.auth.LivePartnerAuthActivity exported=true, VIEW/BROWSABLE, scheme=ikwaipartner host=auth

## Consequência
Depois de encerrar o lease atual, CHAT 1 deve priorizar UM probe curto dos componentes realmente exported=true, começando por TinyUserInfoActivity/TinyGoogleSSOActivity e, separadamente, gateways deeplink. Isso é mudança causal válida em relação ao run 37388231997, que testou cinco Activities internas não-exportadas. Não usar KwaiAuth/OpenAuth como prova de login do usuário sem observar UI/identidade; podem ser fluxos OAuth de terceiros.