# Item fixo 9 — supervisão QA P0 e entrega externa de alertas homologadas
STATUS: PROVEN
AREA: architecture/qa-p0-supervision-alerts
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40782057532
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40782057532/job/123145935173
COMMIT: dd061c0b994b5f8d0dca1be0396032d428007385
SUPERSEDES: 20261028-qa-p0-hosted-alert-running.md
OWNER: ChatGPT AOI item fixo 9
LEASE: ENCERRADO; validação terminal feita sem publicações.

## Baseline e falha causal corrigida
- QA Windows preexistente: GitHub run 40775681413/123124249088 SUCCESS, marcador `CORTES_QA_ROUTER_OK observations=2 opened=0 sources_failed=0`; rota de WordPress via SSH autorizado permanecia no computador. Incidente real #1810 continha fingerprint P0 + URL da fonte, o controlador entregou ao executor e registrou diagnóstico sem afirmar reparação.
- Forgejo Hostinger sandbox isolado: QA não publicador run interno 243 SUCCESS, seis contratos adicionais 245–251 SUCCESS, agenda QA 12/12h registrada. QA Forgejo é independente do Codeberg, mas seu sucesso não equivale a postagem de alerta no GitHub.
- PR #1819 acrescentou ao watchdog GitHub existente um job Ubuntu hospedado sem checkout, sem Windows, sem Codeberg e sem segredos de publicação. A primeira execução real 40781660084/job 123144589898 SUCCESS identificou duas falhas reais e confirmou issues abertas #1780 e #1728, sem criar duplicatas: `QA_P0_CLOUD_MONITOR=PASS candidates=2 verified=2 opened=0`.
- PR #1820 acrescentou entrega por comentário em incidente real aberto, com fingerprint estável, no máximo um comentário novo por execução, GET readback e concorrência exclusiva do job externo. O run 40781907431 ficou PENDING porque a antiga trava de concorrência global de `push` aguardava a rota Windows de run anterior: isto não foi interpretado como sucesso do fallback.
- PR #1821 resolveu essa dependência causal: `push`/dispatch passam a ter grupo distinto por `github.run_id`, o agendamento preserva exclusão mútua, a job Windows mantém seu próprio grupo serial e o job cloud mantém lock exclusivo.

## Prova real decisiva
- Run 40782057532, JOB 123145935173, `cloud-alert-redundancy`, terminou **SUCCESS** em **Hosted Compute Agent** na região centralus / Azure, imagem Ubuntu 24.04, GitHub Token: Actions read, Contents read, Issues write. Runner Windows da mesma workflow permanecia QUEUED sem impedir a conclusão independente da job cloud.
- Marcadores efetivamente gravados no job log:
  `QA_P0_CLOUD_DELIVERY_READBACK=PASS issue=1780 source_run=40779745214 created=false`
  `QA_P0_CLOUD_ALERT_DELIVERED=PASS issue=1780 comment=6482589037 created=true`
  `QA_P0_CLOUD_DELIVERY_READBACK=PASS issue=1728 source_run=40774319720 created=false`
  `QA_P0_CLOUD_MONITOR=PASS candidates=2 verified=2 opened=0 alert_receipts=1 alert_comments_sent=1`
- Confirmação independente adicional: GitHub REST GET `/repos/UniversoAnthares/anthares-kwai-runner/issues/comments/6482589037` retornou o comentário realmente publicado sob a Issue #1780, contendo `[QA-P0-CLOUD-ALERT] 51368506b96f0eb701db75e9` e o run de origem 40779745214. Issue #1780 permanece **OPEN**; a falha continua sob o item 16.
- Os alertas usam exatamente o mesmo SHA256 fingerprint de 24 hex do roteador Windows (`gha|repo|workflow|conclusion|UTC-day`) e excluem ações de publicação. No run terminal foram **0 tickets duplicados, 1 comentário real e 1 receipt GET**.

## Aceitação específica do item fixo 9
Supervisor/alertas independentes **PROVEN**: GitHub Actions hospedado executa e envia alerta P0 real com readback, mesmo com job Windows queued; Forgejo mantém QA não publicador agendado e homologado, GitHub Issues permanece autoridade única para incidentes, sem Codeberg. Nenhum teste repetitivo, serviço, cron novo, quota paga, mídia ou publicação foi criado. O monitor Windows e a leitura autenticada do WordPress foram preservados como camada independente específica.

LIMITES: resolver as falhas concretas, reconciliar publicações UNCERTAIN e encerrar tickets P0 é exclusivamente item fixo 16. Os demais publicadores e a promoção geral do Forgejo permanecem em seus itens. Um job Windows legado ainda pode estar queued e exige acompanhamento normal; seu estado não invalida a prova cloud hospedada.
