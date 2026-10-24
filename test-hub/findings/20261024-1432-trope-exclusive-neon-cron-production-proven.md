# Enciclopédia Narrativa — cron Neon exclusivo autenticado: produção comprovada
STATUS: PROVEN
AREA: wordpress-enciclopedia
DATE: 2026-10-24
RUN: Neon scheduled 2026-10-24T18:30:00Z (log neon-function/tropescron)
JOB: ency-item11-manual; Neon deployment 3
COMMIT: anthares-wordpress 7ae9735f6b50148fc950630132ae9ba914a8bcab
SUPERSEDES: test-hub/findings/20261024-1421-lease-trope-exclusive-activation-chatgpt.md

## Objetivo
Substituir o fallback global WP-Cron pelo acionador exclusivo autenticado Neon -> WordPress sem duplicidades, sem afetar outros plugins, com rollback.

## Resultado
PROVEN no ambiente de produção. WordPress implementou guard reversible em class-anthares-trope-publisher.php via PR #193 (merged), SHA-256 vivo ec47c42de71b8f33403ce155ec9f30e0315b0fa7dbfbb26817ad13f503e9f228. Backup do original: /home/u566597497/.anthares-trope-backups/publisher-before-exclusive-cutover-20261024.php. PHP 8.3 lint aprovado e arquivo original comprovado SHA-256 8537f9ba3ef184cd655d72893c1b9bafa6a02c5703a32f7ee5fb4fd813fb19d3. Manifest QA na branch 594/594 PASS pelo titular; orquestrador PHP no checkout principal inalterado 11 PASS.

Neon tropescron deployment 3 completed, runtime nodejs24, ambiente TROPE_CRON_TOKEN mantido e não exposto. O trigger ORIGINAL permaneceu o único: trigger-fbc8d4bf-fa79-455b-9418-111bd3bbcf96, nome novo tropes-15min, cron */15 * * * *, enabled true, version 7176610. Código dedicado GitHub SHA dfae1d82cfaf33b14a1f3c01e87452000c6784b9. Não foi criado nenhum segundo trigger.

WordPress opção anth_trope_external_cron_enabled_v1=1, nativo anth_trope_daily_tick AUSENTE da lista WP-Cron, mas anth_trope_daily_ledger e anth_trope_editorial_review_tick ainda agendados. POST sem autenticação no WordPress retornou HTTP 403; requisição pública sem contexto de trigger à função Neon retornou 403.

## Evidência decisiva do disparo real
Neon logs 2026-10-24T18:30:01Z invoke begin, 18:30:02Z app log {"scheduled_at":"2026-10-24T18:30:00Z","status":200,"state":"not_due"} e invoke end; horário local America/Campo_Grande 14:30. A opção WordPress anth_trope_last_neon_delivery_v1 contém at=2026-10-24T18:30:02+00:00, scheduled_at=2026-10-24T18:30:00Z, state=not_due e invocation_id; anth_trope_publisher_last_neon_cron_v1 contém at=2026-10-24T18:30:02+00:00, origin=neon_schedule. Corresponde a uma entrega agendada AUTENTICADA, não a uma execução manual. O resultado not_due é normal por teto e grade de horários e prova execução sem gerar post indevido.

O ledger do WordPress em 18:30:02Z registrou 2026-10-24: 5/10, errors=0; 2026-10-23: 10/10, errors=0. O heartbeat nativo pré-corte foi de 18:10:53Z; após o corte não há evento nativo agendado. Nenhum sinal de disparo duplo.

## Contingência / rollback
Se ocorrer falha de autenticação ou indisponibilidade futura: (1) desabilitar ÚNICO trigger existente; (2) definir anth_trope_external_cron_enabled_v1=0; o guard restaura o agendamento anth_trope_daily_tick; (3) restaurar na função Neon o bundle versionado anthares-enciclopedia-narrativa/cron/neon/wpcron-fallback.mjs com env preservado; (4) renomear ÚNICO trigger de volta para tropes-wpcron-15min e reativar; (5) verificar HTTP 200 /wp-cron.php e ausência de duplicidade. Não criar segundo trigger e não repetir publicação de estado incerto. O rollback está documentado, não foi acionado.

## TEST_VALIDITY
SHA e opções de produção e mesmo trigger verificados antes e após; uma única entrega real Neon casou com marker WordPress e origin. Lease encerrado com evidências; implantação aceita. Monitoramento diário e indexação Google são itens independentes, não declarados concluídos por este teste.
