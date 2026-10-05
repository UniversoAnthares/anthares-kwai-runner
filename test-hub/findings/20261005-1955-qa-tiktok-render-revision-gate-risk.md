# TikTok Render revision gate may be stale-environment harness
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388273031
JOB: 112026953805
COMMIT: c7a84b8a44e440beedec9fe8baee7e887e6b34fc
SUPERSEDES: none

## Objetivo
Auditar por que o session restore probe continua aguardando mesmo após a API Render confirmar o deploy exato live.

## Resultado
A API Render já prova que commit fc26d51a... está live. Porém /health do serviço não deriva revision do deploy; service.py retorna `os.getenv("WORKER_RUNTIME_REV","unknown")`. O workflow espera que esse valor seja exatamente fc26d51a... por até 400 s. Se WORKER_RUNTIME_REV não for atualizado junto de cada deploy, o gate pode expirar apesar de a revisão correta estar ativa.

## Evidência decisiva
Render API: deploy dep-db232vvlot8c73dl85o0, commit fc26d51a..., status live, finishedAt 23:25:09Z. Código render-tiktok-worker/service.py: /health -> revision=os.getenv("WORKER_RUNTIME_REV","unknown"). Workflow tiktok-real-publish.yml compara esse campo com fc26d51a... e dorme 10 s até 40 vezes.

## Consequência
Se run 37388273031 terminar RENDER_REVISION_NOT_READY, classificar como TEST INVALID/harness revision-marker, não como falha de sessão. Próxima correção deve usar prova de deploy confiável (Render deploy ID/commit, ou marcador de build realmente atualizado automaticamente) e não esperar >5 min por env estático. Não reiniciar o mesmo probe sem essa mudança causal.