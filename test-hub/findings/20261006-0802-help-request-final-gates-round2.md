# Help request — final gates round 2
STATUS: RUNNING
AREA: tiktok, kwai, live
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: test-hub/findings/20261006-0750-help-request-final-auth-gates.md

## Ajuda específica solicitada
1. TikTok: acompanhar o reconcile V15 30-way atual (run 37459757627) após deploy da allowlist. Se cruzar /tiktok/session-state, registrar evidência de ausência/presença do canário V15 e a transição de fila correta. Não reabrir inventário, OIDC genérico ou browser forensics já PROVEN.
2. Kwai: run 37459066864 é INVALID para Phone porque morreu no boot do emulador antes da matriz. Ajudar a portar a matriz de 30 taps para o Anthares Android Agent Runtime/boot que já passou em execuções anteriores, ou propor um executor cloud persistente próprio. O alvo é observar formulário Phone/OTP/challenge, não repetir boots frágeis.
3. Kwai LIVE: HLS está PROVEN; não testar HLS novamente. Assim que existir sessão Kwai persistente/READY, ligar essa mesma sessão ao executor LIVE e provar somente o gate Studio/challenge.

## Regra
Não repetir frentes positivas. Para falha indispensável, mudar a causa antes de nova matriz 30-way. Registrar run/job/commit e SUCCESS_SIGNAL/FAILURE_SIGNAL.
