# Kwai exported auth runtime reached app but not login UI
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37389007878
JOB: 112029351135
COMMIT: 2d6a094237329dbc196902b2c0bede40881daff9
SUPERSEDES: test-hub/findings/20261006-0050-lease-kwai-exported-auth-runtime.md

BASELINE_PROVEN: test-hub/findings/20261006-0048-kwai-auth-intent-contracts-proven.md
FAILED_AVOIDED: internal non-exported Activities were not direct-started.
SUCCESS_SIGNAL: exact exported URI reaches login foreground, EditText, or explicit login/email/phone/password UI.
FAILURE_SIGNAL: all exact exported routes resolve/start without login UI.
TEST_VALIDITY: Kwai installed; each URI invocation logged; UI dump collected.

## Resultado
Os URI contracts exportados iniciaram o Kwai, mas nenhum produziu UI de login. ikwai://authorization caiu em TinyLaunchActivity e ficou coberto pelo diálogo de notificação; kwai://authorization, ikwaipartner://auth e com.kwai.video://auth chegaram ao feed/home. EDITTEXT_COUNT=0 em todos.

## Evidência decisiva
Job 112029351135: AM_RC=0 para as rotas; kwai://authorization -> TinyNativeHomeActivity com Home/Discover/Inbox/Profile; ikwaipartner://auth -> TinyNativeHomeActivity; com.kwai.video://auth -> TinyNativeHomeActivity; FAILURE_SIGNAL=EXPORTED_ROUTES_NO_LOGIN_UI.

## Consequência
Não repetir estes mesmos deep links. O caminho de gateway exported direto não entrega login nas condições testadas. Próximo avanço kwai-login deve mudar causalmente para navegação interna state-driven/Accessibility, começando por fechar o diálogo de notificação e entrar por Profile/controles reais, ou integrar o Anthares Agent ao FSM. O resultado não prova que login interno seja impossível.