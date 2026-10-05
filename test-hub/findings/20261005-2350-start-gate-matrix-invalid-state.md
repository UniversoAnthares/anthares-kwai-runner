# Start-gate matrix invalidated by nondeterministic entry state
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37383491793
JOB: 20-route matrix
COMMIT: 1bbab30672337f9c0762919d501de32dd9591ab4
SUPERSEDES: none

## Objetivo
Comparar 20 mecanismos para consumir especificamente o gate Start now.

## Resultado
A matriz não isolou o gate de forma válida. Os quatro jobs verdes (high-center, tap-wait10, low-center, center) registraram ALREADY_MAIN=1 antes de executar sua técnica, portanto não provam que essas técnicas vencem Start now. Diversos jobs vermelhos terminaram NO_START_GATE=1, isto é, nem chegaram ao estado-alvo. O onboarding/estado inicial varia entre emuladores.

## Evidência decisiva
high-center/tap-wait10/low-center/center: ALREADY_MAIN=1.
node/double/tap-restart e vários outros: NO_START_GATE=1 -> exit 20.
Logo, conclusão do job correlacionou com o estado inicial, não com a técnica da variante.

## Consequência
Não promover nenhuma técnica desta matriz como solução de Start now. Próximos probes devem ser state-driven: reconhecer permission, interest, Start now, main nav, resource downloading e feed real; agir conforme o estado observado e registrar transições. Só ramificar experimentos depois de atingir um estado-alvo comum.
