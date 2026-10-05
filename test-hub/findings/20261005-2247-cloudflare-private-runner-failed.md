# Segundo deploy Cloudflare falha antes da execução útil
STATUS: FAILED
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/37380766270
JOB: 112001851902
COMMIT: eca48b62c1c151a077d119b38a74b9cbe16aa743
SUPERSEDES: test-hub/findings/20261005-2242-cloudflare-dedupe-deploy-running.md

## Objetivo
Publicar no Worker a barreira central de overlap após endurecer o workflow de deploy.

## Resultado
O novo run foi criado e terminou failure em cerca de quatro segundos, mesmo com workflow_dispatch, id-token, validação do token e wrangler fixado. A API reporta o job deploy como failure. O padrão de falha imediata permanece anterior a uma execução útil do deploy.

## Evidência decisiva
Run 37380766270, job 112001851902, status completed/conclusion failure, criado 22:10:43Z e finalizado 22:10:47Z. O mecanismo de obtenção de logs retornou indisponível para esse job, portanto a causa interna exata não foi inventada.

## Consequência
Não repetir simplesmente o deploy pelo mesmo runner privado. A próxima tentativa deve mudar o mecanismo de execução (runner público/hub ou deploy direto por outro executor autorizado). A barreira central continua PARTIAL em produção.
