# Login UI Inspector verde, mas preso no diálogo Android de notificações
STATUS: PARTIAL
AREA: android
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380670886
JOB: 112001527688
COMMIT: 452cdf5cf0358a72f984321ac39e28a2293babbe
SUPERSEDES: none

## Objetivo
Inspecionar a UI de login/Profile depois dos avanços de navegação.

## Resultado
O workflow terminou success e gerou artefato, porém todos os snapshots inspect-stage-0 até inspect-profile exibiram exclusivamente o diálogo nativo "Allow Kwai to send you notifications?". Portanto o inspector não chegou a testar a UI de login do Kwai.

## Evidência decisiva
Em todos os snapshots relevantes o package/resource-id é com.android.permissioncontroller e aparecem permission_allow_button / permission_deny_button. O log termina INSPECT_COMPLETE, mas não há estado de Profile/login do Kwai.

## Consequência
Não usar o verde deste run como prova de login. Qualquer inspector subsequente deve limpar o permissioncontroller antes de coletar snapshots. A rota Profile continua apoiada pelos runs 37379937689 e 37380001963; este run apenas revela falha do mecanismo de inspeção.
