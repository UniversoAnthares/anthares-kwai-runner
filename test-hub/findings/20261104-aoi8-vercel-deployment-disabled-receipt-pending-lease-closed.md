# AOI #8 — recibo CI histórico: controlador Vercel indisponível, execução terminal sem duplicação
STATUS: PARTIAL
AREA: github-ci/gitlab-quota-successor-confirmation
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T21:01:30.424Z
ITEMS: [8]
LEASE_OWNER: chatgpt-aoi8-20261104
LEASE_AREA: github-ci/gitlab-quota-successor-confirmation
LEASE: CLOSED
SUPERSEDES: lease-20261104-aoi8-historical-receipt-confirmation.md
SOURCE_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2011
SOURCE_COMMIT: f9f0d27ee805c784a015c9aceb961b63c36d3c85
PAYMENT_OR_PLAN_CHANGE: NONE
PUBLISHER_EFFECT: NONE

## Fonte e patch
Neon `public.anthares_ci_quota_attempts`: 18 FALLBACK_CONFIRMED, 1 FALLBACK_SUBMITTED para `gitlab:87307248:3005500025` (SHA `94ba06e628d0b1ba0bdfeabbdfd9a00b86508759`, source_terminal=true, dispatch_accepted=true, generation=2).
GitHub run 40942048873 é `workflow_dispatch`, `completed/success`, `.github/workflows/gitlab-quota-fallback.yml`, e display_title tem SHA exato. PR #2011 foi integrada no main e acrescentou modo `reconcile_only` com campos exatos e `dry_run=true` por padrão, preservando controlador OIDC Vercel, CAS/Neon e exclusão de novo dispatch; retirou a pesquisa GitLab de 72h indisponível e gatilho push do watcher. Quatro testes isolados da função nova passaram; suíte completa e CI não foram executados nesta rodada.

## Tentativa única e diagnóstico
- GitHub run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41911390227, job 126859569090, em 2026-11-04: recebeu `ANTHARES_RECONCILE_ONLY=true`, componentes/IDs/SHA esperados, encerrou failure com `EXACT_RECONCILIATION_UNCONFIRMED_NO_DISPATCH`. Não houve segundo disparo de resgate.
- O comando de controle remoto respondeu erro interno após possível efeito; o estado foi reconciliado por fontes independentes, identificando esse único run real. O workflow `gitlab-quota-watcher.yml` foi consultado novamente e ficou `disabled_manually`, exatamente como antes.
- Consulta direta `GET https://anthares-ci-quota-controller.vercel.app/api/health` retornou HTTP 402, `X-Vercel-Error=DEPLOYMENT_DISABLED`; deployment consta READY no histórico do Vercel, mas a rota em produção está desabilitada. Logs de função vazios. Isso explica o impedimento técnico, sem provar detalhadamente a razão administrativa/financeira do bloqueio.
- Readback Neon após execução: o mesmo registro permanece FALLBACK_SUBMITTED, generation=2, successor_run_id nulo. Nenhum replay, SQL direto, publicação ou pagamento efetuado.
- GitLab API retornou 403/404 em auditorias recentes; não houve contorno dessa recusa nem nova leitura da pipeline.

## Próximo gate
Se a disponibilidade gratuita do endpoint original voltar: conferir `/api/health=200`, lease e registros atuais antes de outra tentativa autorizada e singular; respeitar eventual reset de quota. Alternativa independente só com o MESMO contrato OIDC, verificação de run/flow/SHA, CAS, quota própria comprovada e autorização operacional prévia. Nunca alterar Neon diretamente para fingir confirmação, nem reativar workflow agendado. Item #8 continua PARCIAL até recibo autenticado e homologação real dos demais cancelamentos por quota.
