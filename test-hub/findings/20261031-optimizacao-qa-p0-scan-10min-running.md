# OTIMIZAÇÃO — redução reversível da cadência do controlador QA P0 (candidato)
STATUS: RUNNING
AREA: health/cortes/qa-p0-schedule
DATE: 2026-10-31 UTC
OWNER: Reestruturação e Otimização / 00 — Auditoria e decisões
LEASE: BRANCH_ONLY; revisão concorrente de main requerida antes do merge; nenhum lease de produção reivindicado.
BASELINE_PROVEN: GitHub main 7a44b8c64f83fd4498d81c18d3d773424a844467; workflow blob 648f2b784e01492b901f905a72430e07ab359a5b; GitLab main contém o mesmo blob. Test Hub 20261029-item16-qa-p0-fingerprint-dispatch-dedupe-partial.md preservado. Mais de 100 incidentes QA P0 abertos na consulta.
FAILED_AVOIDED: sem publicação, redisparo QA/CI manual, fechamento de incidente, exclusão de workflow ou alteração de Windows.
SUCCESS_SIGNAL: YAML válido; eventos issues opened/reopened/labeled, push, workflow_dispatch, pull_request preservados; watchdog de 5min e 13,43/h intacto; controller reduzido de 5 para 10 min; logs de backlog coerentes; 288→144 oportunidades/dia; conferência de detecção imediata por evento e backlog antes da promoção.
FAILURE_SIGNAL: incidente novo sem dispatch por evento, crescimento anormal do backlog, duplicação de tentativas, perda de alerta. Reversão antes da promoção.
TEST_VALIDITY: patch estático em branch isolada e revisão por PR draft; nenhuma mídia, incidente sintético ou arquivo no PC.
CUSTO: zero infraestrutura nova; economia de 144 horários programados/dia, ainda sem mensuração de minutos.
ROLLBACK: restaurar somente cron original '*/5 * * * *' e mensagem de backlog original com SHA/lease conferidos.
GOVERNANCA: manifest Windows 84905aefc5589d17 diverge do GitHub 223433740e807a90; PR governança #48 altera os mesmos quatro arquivos. Reconciliação permanece separada.
AOI: OTIMIZAÇÃO transversal, associada ao item 16; estado terminal do AOI inalterado.
