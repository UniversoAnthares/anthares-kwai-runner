# TikTok real publish workflow still lacks production acceptance gates
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-05
RUN: none
JOB: static-readonly-audit
COMMIT: c7a84b8a44e440beedec9fe8baee7e887e6b34fc
SUPERSEDES: none

## Objetivo
Auditar o caminho workflow_dispatch de .github/workflows/tiktok-real-publish.yml sem interferir no probe de sessão em execução.

## Resultado
O push atual é seguro: session-restore-probe roda e o job publish fica skipped. Porém o caminho real workflow_dispatch ainda não satisfaz aceitação de produção. Ele usa BASE=https://anthares-tiktok-worker.onrender.com enquanto a cadeia de sessão/health usa anthares-tiktok-render-rootless.onrender.com; não valida sessão/identidade imediatamente antes de publicar; e considera sucesso apenas x.ok retornado por /publish, sem prova independente de que um novo post apareceu na conta correta nem fechamento explícito do ledger central.

## Evidência decisiva
Workflow atual: publish só roda em workflow_dispatch; baixa mídia, POSTa /publish e imprime TIKTOK_REMOTE_PUBLICATION_CONFIRMED quando result.json contém ok=true. Não há etapa posterior de profile/post verification, account identity, queue complete/reconcile ou remote post id obrigatório.

## Consequência
CHAT 3 não deve classificar TikTok production-PROVEN a partir de um futuro job verde deste publish. Antes do canário real, alinhar endpoint com o executor efetivamente ativo, exigir identidade da conta correta, confirmação independente do novo post e integração com ledger/estado incerto. O probe 37388273031 continua válido apenas para sessão/identidade porque o job publish está skipped.