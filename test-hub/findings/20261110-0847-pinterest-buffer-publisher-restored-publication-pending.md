# CORTES Pinterest/Buffer — recuperado para agendar; prova pública pendente
STATUS: PARTIAL
AREA: pinterest-buffer-publish
DATE: 2026-11-10 UTC
ITEMS: [16,21]; NUCLEO: CORTES
LEASE: CLOSED
SUPERSEDES: test-hub/findings/lease-20261110-0826-pinterest-buffer-reactivation.md
OWNER: chatgpt-pinterest-restore-20261110-0826
MAIN_CODE_FIX: PR #2296; merge 7aa19f3c9a50fcbf408c8540fd29777ab9c0d256

## Evidências
- Publicador Pinterest existente reativado no GitHub; GitLab peer do workflow tinha blob idêntico.
- Identidade exata lucasyahn; canal Buffer 6ad8a46d778b240e2f79a40f; board 819514532133906920.
- Antes: Neon 20 confirmed, 208 failed, 154 queued, 10 uncertain; quatro queued MP4 HEAD HTTP200 video/mp4.
- Cooldown Buffer API 429 expirado e issue #507 já encerrada em 2026-11-09 por Pin público anterior.
- Run 42816051468: modo read-only SUCCESS, autenticação Buffer + Neon/OIDC, zero novos Pins.
- Run 42816487401: SUCCESS, board confirmada via segundo resolver, primeiro SCHEDULED_IN_BUFFER.
- Run 42818066473: SUCCESS, segundo SCHEDULED_IN_BUFFER após push do QA, sem duplicação.
- Run 42817864059: testes unitários do QA passaram; ramo não-main recusado por OIDC Neon HTTP401, zero Pin adicional.
- PR #2296: incidente HTTP429 somente reabre diante de novo cooldown real; reconcile_only gera PASS_NO_NEW_PIN.
- Run 42818451477: SUCCESS em main/read-only; PASS_NO_NEW_PIN, issue #507 permaneceu closed.
- Depois: Neon 20 confirmed, 208 failed, 152 queued, 12 uncertain; 2 recém-agendados no Buffer aguardam prova pública.

## Aceite ainda pendente
- Obter ao menos um link Pinterest público de um dos dois agendamentos, com status sent oficial e confirmação CAS Neon.
- Confirmar ao menos uma execução natural agendada do workflow reativado.
- Não reenviar os registros antigos uncertain nem os failed históricos sem reconciliação explícita.
- Nenhum novo serviço, cron, runner, segredo ou media no PC foi criado.
- Test Hub README GitLab/GitHub apresentava divergência de blob e não foi alterada.
- O lease foi encerrado; o publicador oficial permanece ativo. Não registrar DONE antes do recibo externo.
