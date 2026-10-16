# Reconciliação Fases 6–8

STATUS: PROVEN / SUPERSEDED
DATE: 2026-10-15

## Fase 6 — failover GitHub ↔ GitLab e dedupe cross-provider
PROVEN. Já comprovada durante a homologação da Fase 4: o job `ara-phase4-cross-provider-20261015-2320` executou pelo GitHub; o mesmo `job_id` entregue depois pelo GitLab reutilizou o receipt persistido e não reexecutou a mutação. Failback GitLab também executou job novo com sucesso.

## Fase 7 — recuperação SYSTEM autônoma
PROVEN. Já comprovada durante a Fase 3: supervisor SYSTEM e watchdog ativos; executor morto e supervisor morto foram recuperados automaticamente; exatamente um `v4-c8.exe` permaneceu canônico; timeout/uncertain/idempotência foram preservados sem replay perigoso.

## Fase 8 — WinRemote independente
SUPERSEDED. A política atual proíbe WinRemote, MeshCentral e outros remotes como fallback. Anthares Remote é a única superfície de controle remoto, com Vercel+Neon e filas privadas GitLab/GitHub como redundância interna. Não reabrir F8 salvo decisão explícita do proprietário.

## Próxima pendência real
Fase 9: redundância do Anthares Browser sem Render/TinyFish/Browserless e sem depender de Cloudflare Browser Rendering. Validar a superfície Anthares Browser com pelo menos dois backends elegíveis ou um backend primário mais um fallback independente comprovado.