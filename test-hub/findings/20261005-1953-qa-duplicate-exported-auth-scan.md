# Duplicate exported-auth scan produced no new causal evidence
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388571002 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388585850
JOB: 112027914343 ; 112027964602
COMMIT: 8e90ad7c07e00afde8f6bd74909f0f627950a4ae ; 16b1f14eeb2fd8a51b2fe6a587623ec99d57a0ed
SUPERSEDES: none

## Objetivo
Auditar repetição de teste sob o protocolo do hub.

## Resultado
Dois pushes consecutivos dispararam o mesmo scanner com o mesmo objetivo e ambos terminaram success/TEST_VALIDITY=OK, sem mudança causal relevante entre os resultados. O segundo foi descrito como retrigger após workflow registration, mas o primeiro já havia executado o workflow com sucesso.

## Evidência decisiva
Runs 37388571002 e 37388585850 têm o mesmo workflow e ambos retornam CANDIDATE_COUNT=67, TEST_VALIDITY=OK e o mesmo conjunto relevante de exported flags.

## Consequência
Não disparar terceiro scan. Usar 37388585850 como evidência canônica e avançar para um único teste causal de entrypoint exported. Antes de retrigger, conferir se o run anterior realmente não iniciou/é inválido.