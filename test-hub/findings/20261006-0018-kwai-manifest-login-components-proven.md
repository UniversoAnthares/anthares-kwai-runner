# Kwai manifest exposes concrete login activities
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388030409
JOB: 112026171392
COMMIT: d9a144b23fbca831e4b382aa710549b68d9af77a
SUPERSEDES: test-hub/findings/20261006-0004-lease-kwai-login-manifest-repair.md

BASELINE_PROVEN: test-hub/findings/20261005-2250-kwai-apk-login-resources.md
FAILED_AVOIDED: test-hub/findings/20261006-0001-kwai-login-metadata-harness-invalid.md; missing script was added and aapt validity was enforced. test-hub/findings/20261006-0002-kwai-direct-login-no-runtime-targets.md; runtime launch is deferred until exact manifest names are known.
SUCCESS_SIGNAL: valid aapt execution plus manifest metadata for known login/auth components.
FAILURE_SIGNAL: valid manifest dump contains none.
TEST_VALIDITY: aapt ran, manifest-tree.txt was nonempty, artifact uploaded.

## Objetivo
Obter do Manifest nomes concretos de Activities de autenticação antes de novo teste Android.

## Resultado
SUCCESS_SIGNAL=KNOWN_LOGIN_COMPONENT_DECLARED. O Manifest contém uma superfície de login muito mais direta que os antigos candidatos Tiny*: com.yxcorp.gifshow.login.SplashLoginActivity, PhoneAccountActivityV2, com.yxcorp.gifshow.login.emaillogin.activity.EmailLoginActivity, com.yxcorp.gifshow.login.LoginActivity, com.yxcorp.gifshow.login.activity.CommonLoginActivity e várias Activities auxiliares/SSO. Também contém com.yxcorp.gifshow.authorization.KwaiAuthActivity e LivePartnerAuthActivity.

## Evidência decisiva
Run 37388030409 executou aapt válido, extraiu AndroidManifest.xml e terminou com SUCCESS_SIGNAL=KNOWN_LOGIN_COMPONENT_DECLARED. Linhas 5863-5939 do xmltree incluem as Activities acima.

## Consequência
Abandonar TinyLoginActivity/TinyUserInfoActivity como alvos primários. Próximo teste deve usar somente nomes completos declarados no Manifest e medir separadamente se am start é permitido e se a UI produz EditText/login controls. Prioridade: EmailLoginActivity, LoginActivity, CommonLoginActivity e PhoneAccountActivityV2.
