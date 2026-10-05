# Exported auth URIs resolve but do not expose login UI
STATUS: FAILED
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37389007878
JOB: 112029351135
COMMIT: 2d6a094237329dbc196902b2c0bede40881daff9
SUPERSEDES: test-hub/findings/20261006-0050-lease-kwai-exported-auth-runtime.md

BASELINE_PROVEN: test-hub/findings/20261006-0048-kwai-auth-intent-contracts-proven.md
FAILED_AVOIDED: test-hub/findings/20261006-0028-declared-login-activities-not-exported.md; only exported URI contracts were invoked.
SUCCESS_SIGNAL: exact exported URI reaches Login foreground, EditText, or explicit login/email/phone/password UI.
FAILURE_SIGNAL: all exact exported routes resolve without login UI.
TEST_VALIDITY: Kwai installed; all URI invocations returned AM_RC=0; Activity result and UI dump were collected.

## Resultado
FAILURE_SIGNAL=EXPORTED_ROUTES_NO_LOGIN_UI. ikwai://authorization resolved to TinyLaunchActivity; kwai://authorization, ikwaipartner://auth and com.kwai.video://auth resolved to TinyNativeHomeActivity. All had EDITTEXT_COUNT=0. The lone AUTH_HITS=conta on ikwai was insufficient under the declared success criterion.

## Evidência decisiva
All four am start calls returned Status: ok, so routing itself worked. None produced Login foreground or editable login controls.

## Consequência
Do not repeat these bare exported URI calls. Exported OAuth/auth gateways likely require caller/query context or authenticated authorization state. Return to the PROVEN state-driven MAIN path and investigate the internal event/navigation that invokes LoginActivity, using static call-site analysis and the Anthares Android Agent/accessibility path. Preserve the FSM.
