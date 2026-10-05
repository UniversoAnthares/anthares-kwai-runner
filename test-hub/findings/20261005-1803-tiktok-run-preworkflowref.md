# Run 37378729369 antecede correção workflow_ref
STATUS: SUPERSEDED
AREA: tiktok
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378729369
JOB: 111994756820
COMMIT: ab3565d8957b01f180dd420a0c218a23f227d411
SUPERSEDES: test-hub/findings/20261005-1759-tiktok-oidc-workflow-ref.md

## Objetivo
Determinar se a falha visível mais recente testou de fato a correção workflow_ref.

## Resultado
Não. O run começou às 21:52:12Z; o commit corretivo surgiu às 21:59:13Z e o deploy só ficou live às 22:00:40Z.

## Evidência decisiva
Run 37378729369 antecede o deploy dep-db21rd2jnfac73ejbf6g live do commit ab3565d8.

## Consequência
Não classificar workflow_ref como FAILED com esse run. Executar novo probe OIDC criado após o deploy live.
