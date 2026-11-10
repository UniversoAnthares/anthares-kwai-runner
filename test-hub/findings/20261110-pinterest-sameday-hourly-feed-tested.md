# Pinterest CORTES — reposição horária com gate de horários do mesmo dia
STATUS: PARTIAL
AREA: pinterest-buffer-same-day
DATE: 2026-11-10 UTC
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42831209310
JOB: 129881416859
SUPERSEDES: test-hub/findings/20261110-0917-pinterest-buffer-calendar-dueat-confirmed.md
OWNER: chatgpt-pinterest-clipper-daily-20261110

## Evidência de código
- Ref: fix/pinterest-sameday-buffer-feed-20261110, cron 09h08–22h08 MS em dias úteis, com conversão UTC diferenciada nas madrugadas Tue-Sat.
- O publicador continua a enfileirar no máximo um novo post por execução, obedecendo o orçamento global Neon, limite de oito pendências Buffer e a validação editorial.
- Antes de qualquer createPost, consulta autenticada somente leitura de calendário e de reservas scheduled da conta Pinterest. Quando não há janela futura livre no dia local, retorna BUFFER_TODAY_SLOTS_FILLED sem enviar vídeo nem usar vaga amanhã.
- Identidade do canal, timezone e pausa da conta são verificadas; qualquer erro de leitura interrompe a nova criação (fail closed), sem reenviar registros uncertain.

## Teste em branch
- Run 42831209310, etapa de testes: SUCCESS, incluindo cinco testes do gate do mesmo dia e módulos de regressão existentes.
- O passo publisher da execução em branch terminou CORTES_QUEUE_REJECTED_401, esperado porque o Neon/OIDC somente autoriza escrita para main. Zero novo Pin criado nessa execução.
- Merge em main e uma execução de produção com Buffer agendado e depois Pinterest link público/CAS Neon ainda requerem evidência.

## Restrições
- Não usar shareNow, não reenviar trabalhos incertos, não ativar PC, não contratar recursos.
- Limites global Buffer de 20 alocações/dia útil e quota própria da conta continuam aplicados.
- Nenhuma confirmação pública nova ainda comprovada por esta alteração.
