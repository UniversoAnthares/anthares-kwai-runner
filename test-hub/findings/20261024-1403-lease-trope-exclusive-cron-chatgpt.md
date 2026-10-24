# Enciclopédia Narrativa — lease: cron exclusivo Neon
STATUS: RUNNING
AREA: wordpress-enciclopedia
DATE: 2026-10-24
RUN: none
JOB: ency-item11-manual; Neon function tropescron deployment 2
COMMIT: anthares-wordpress main 4e46632e0db215931a3f0c29e8436f60ec145620
SUPERSEDES: none
LEASE_START: 2026-10-24T18:03:00Z
LEASE_EXPIRES: 2026-10-24T18:32:00Z
OWNER: ChatGPT

## Objetivo
Migração isolada do trigger Neon único para endpoint REST exclusivo, com supressão reversível do WP-Cron nativo do publicador. Não afetar cron de outros plugins.

## BASELINE_PROVEN
Preflight local ency-item11-manual PASS v6276158ef2239898; tropescron deployment #2 completed e ambiente TROPE_CRON_TOKEN presente, sem ler valor; trigger fbc8d4bf-fa79-455b-9418-111bd3bbcf96 nome tropes-wpcron-15min ativo */15; option WP segredo com 64 caracteres, endpoint off retorna 503; WP evento anth_trope_daily_tick nativo está agendado. WordPress plugin publisher vivo SHA-256 8537f9ba3ef184cd655d72893c1b9bafa6a02c5703a32f7ee5fb4fd813fb19d3 idêntico ao GitHub blob afab8cfe4bfc40742772442ee0aa7bdb4874c099.

## FAILED_AVOIDED
CLI Neon deploy sem --src falhou sem gravar; não repetir. Usar único trigger, impedir duplicidades, nunca exibir segredo, não alterar outros publicadores.

## SUCCESS_SIGNAL
1. Código WordPress suprime evento nativo quando o endpoint exclusivo é habilitado e o restaura quando desabilitado.
2. Neon código dedicado com env token herdado.
3. Único trigger passa a tropes-15min, sem concorrentes.
4. REST sem token retorna 403 e entrega autenticada da Neon real retorna 200.
5. WordPress anth_trope_last_neon_delivery_v1 e origin neon_schedule correlacionam-se com log Neon sem duplicidade.
6. Rollback para fallback versionado praticável.

## FAILURE_SIGNAL
Drift de produção, env ausente, 403/503 autenticado, deployment falho, trigger duplicado ou desaparecido, origin não identificado.

## TEST_VALIDITY
Verificar IDs, hashes e estado real antes/depois; POST sintético não prova schedule. Invalidar em concorrência. 
## Fechamento
Anexar finding novo append-only com resultados, sem sobrescrever este lease. Expira até 18:32Z.
