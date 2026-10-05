# Stabilized autologin acceptance still cannot expose account field
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37379608085
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37379608085/job/111997876792
COMMIT: 651d9924beb570b02ad08b252533d28695a4d75c
SUPERSEDES: none

## Objetivo
Validar em Android descartável real o autologin estabilizado que incorpora a travessia adaptive e a tentativa restart-after-nav para alcançar Profile/login e autenticar.

## Resultado
O Android iniciou, o vault foi obtido, as credenciais estavam presentes, KVM foi habilitado e o Kwai chegou a KWAI_LAUNCHED. A etapa real de aceitação permaneceu executando por cerca de oito minutos e terminou com AUTOLOGIN_FAILED_RC=3. No código atual, RC=3 significa que, após as rotas semânticas e o fallback determinístico, nenhum EditText de conta/login ficou disponível para preenchimento.

## Evidência decisiva
Job 111997876792: Fetch validated Kwai vault=success; Verify credentials exist=success; Enable KVM=success; Real disposable Android acceptance=failure. Log decisivo: KWAI_LAUNCHED seguido por AUTOLOGIN_FAILED_RC=3 e exit code 3.

## Consequência
Não repetir o mesmo fluxo restart-after-nav/autologin sem alteração causal. Android, instalação e launch continuam comprovados e não são a causa desta falha. O próximo experimento deve observar e preservar XML/screenshot imediatamente antes do RC=3 e comparar com a matriz Profile/login, priorizando uma rota que comprovadamente exponha um controle de login/EditText antes de tentar preencher credenciais.
