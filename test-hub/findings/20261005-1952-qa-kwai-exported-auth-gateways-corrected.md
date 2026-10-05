# Corrected exported Kwai auth gateway set
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388585850
JOB: 112027964602
COMMIT: 16b1f14eeb2fd8a51b2fe6a587623ec99d57a0ed
SUPERSEDES: test-hub/findings/20261005-1948-qa-kwai-exported-auth-gateways.md

## Objetivo
Corrigir a extração QA anterior usando o scanner dedicado que associa exported ao bloco exato de cada Activity.

## Resultado
TinyUserInfoActivity é exported=true. TinyGoogleSSOActivity é exported=false; a extração QA anterior associou incorretamente um exported adjacente e fica supersedida neste ponto. Também permanecem exported=true OpenAuthActivity, KwaiAuthActivity e LivePartnerAuthActivity, conforme scanner/Manifest.

## Evidência decisiva
Run 37388585850: TinyGoogleSSOActivity EXPORTED_RAW=0x0; TinyUserInfoActivity EXPORTED_RAW=0xffffffff; OpenAuthActivity, LivePartnerAuthActivity e KwaiAuthActivity EXPORTED_RAW=0xffffffff; TEST_VALIDITY=OK.

## Consequência
Próximo probe direto deve priorizar TinyUserInfoActivity como único Tiny login/user candidate comprovadamente exported entre esses dois. TinyGoogleSSOActivity não deve ser testada por am start externo. Gateways OpenAuth/KwaiAuth/LivePartner continuam candidatos separados e não são prova de login de usuário por si só.