# Autologin real com rota adaptativa ainda termina RC=3
STATUS: FAILED
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378867229
JOB: 111995229791
COMMIT: 1d35dce9f93fa6cf255a443a067f95bfee870056
SUPERSEDES: none

## Objetivo
Executar um único E2E credenciado real usando a rota adaptativa até Profile e então confirmar autenticação com kwai_auth_probe.py.

## Resultado
Vault, credenciais presentes, KVM, instalação, launch e aceitação Android passaram. O autologin executou por cerca de 6m25s e terminou AUTOLOGIN_FAILED_RC=3. RC=3 no script significa que nenhum campo editável de conta foi encontrado mesmo após as rotas alternativas. O auth probe não chegou a executar.

## Evidência decisiva
Log: KWAI_LAUNCHED; ANDROID_EXECUTOR_ACCEPTED; depois AUTOLOGIN_FAILED_RC=3 e exit code 3. O workflow não reportou senha incorreta nem challenge; a falha ocorreu antes do preenchimento de login.

## Consequência
NÃO repetir o mesmo autologin adaptativo. A próxima investigação deve instrumentar a UI pós-onboarding/Profile sem credenciais: capturar somente texto, resource-id, classe e estado clicável por transição, identificar semanticamente o controle que abre login e só então fazer novo E2E credenciado. Não classificar credenciais como causa.
