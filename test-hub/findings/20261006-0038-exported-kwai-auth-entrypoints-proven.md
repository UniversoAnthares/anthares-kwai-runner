# Exported Kwai auth entrypoints proven in Manifest
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388571002
JOB: 112027914343
COMMIT: 8e90ad7c07e00afde8f6bd74909f0f627950a4ae
SUPERSEDES: test-hub/findings/20261006-0030-lease-kwai-exported-auth-scan.md

BASELINE_PROVEN: test-hub/findings/20261006-0018-kwai-manifest-login-components-proven.md
FAILED_AVOIDED: test-hub/findings/20261006-0028-declared-login-activities-not-exported.md
SUCCESS_SIGNAL: at least one exported or intent-filtered auth/account/login/profile Activity/alias.
FAILURE_SIGNAL: no auth-related external entrypoint.
TEST_VALIDITY: aapt parsed full Manifest and TEST_VALIDITY=OK.

## Resultado
Há entradas externas concretas. Os candidatos Kwai mais relevantes são com.yxcorp.gifshow.oauth.activity.OpenAuthActivity, com.yxcorp.gifshow.auth.LivePartnerAuthActivity e com.yxcorp.gifshow.authorization.KwaiAuthActivity, todos com intent-filter e EXPORTED_RAW=0xffffffff. TinyUserInfoActivity também aparece exported=true sem intent-filter.

## Evidência decisiva
Run 37388571002: OpenAuthActivity INTENT_FILTER=True EXPORTED_RAW=0xffffffff; LivePartnerAuthActivity idem; KwaiAuthActivity idem; TEST_VALIDITY=OK.

## Consequência
Próximo teste Android deve usar apenas esses entrypoints exportados. Primeiro capturar exatamente actions/categories/data schemes do Manifest; depois invocar intents compatíveis e observar se chegam ao fluxo interno de login.
