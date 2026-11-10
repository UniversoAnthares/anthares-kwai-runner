# Pinterest Buffer: horários dueAt verificados e workflow de auditoria restaurado
STATUS: PARTIAL
AREA: pinterest-buffer-readonly-calendar
DATE: 2026-11-10 UTC
LEASE: CLOSED
SUPERSEDES: test-hub/findings/lease-20261110-0912-pinterest-calendar-dueat.md
OWNER: chatgpt-pinterest-0912

## Evidências
- Workflow de calendário já existente, .github/workflows/buffer-cortes-live-calendar.yml, estava disabled_manually. Foi habilitado unicamente para uma auditoria autorizada, somente leitura, e devolvido a disabled_manually.
- Run 42822476463 SUCCESS, consulta GraphQL autenticada Buffer, nenhuma mutação de post, identidade Pinterest lucasyahn e board 819514532133906920 verificados, queue paused=false, timezone America/Campo_Grande.
- Buffer BOOKED 6af30eae85810493942e8171, dueAt=2026-11-10T14:49:00Z (10h49 local).
- Buffer BOOKED 6af3114d6202102f59bf7128, dueAt=2026-11-10T15:04:00Z (11h04 local).
- Um segundo exame pós-auditoria confirmou workflow oficial publisher activo e calendário audit disabled_manually.
- Neon 20 confirmed, 208 failed, 152 queued, 12 uncertain às 09h10 local; dois novos Buffer scheduled permaneciam sem link público.
- Cron oficial Pinterest: 38 */3 * * * (próximo previsto 15h38Z = 11h38 local). Execução natural ainda não comprovada após reabilitação.
- Tarefa avulsa de reconciliação após a janela de entrega criada para 11h50 local, id Automation_a3fff3c8afdc81918cb79e583e58c4a8, habilitada; disparo efetivo futuro ainda não comprovado.

## Aceite e limites
- Pendente: Buffer reportar sent, URL pública pinterest.com/pin/ID e CAS Neon confirmed por conta lucasyahn.
- Não usar editPost shareNow nem reapresentar registros uncertain; preservar cron/intervalos de publicação da conta.
- Nenhum arquivo de mídia foi baixado, serviço adicional de hosting criado ou segredo acessado fora do runtime autorizado.
- Calendar QA lease encerrado e workflow original restaurado. O publisher segue em operação; ainda não rotular núcleo CORTES como DONE.
