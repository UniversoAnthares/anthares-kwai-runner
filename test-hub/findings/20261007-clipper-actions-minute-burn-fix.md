# Clipper private Actions minute burn — schedule reduction
STATUS: PARTIAL
AREA: github
DATE: 2026-10-07
RUN: multiple failure runs dying in ~3s (e.g. 37632836923)
JOB: publish_owned / Clipper Cloud
COMMIT: ebdd5c788ab70644837fb4ed81adef0c4beda9f7 (storage), cea5ce876c2fd5f3f9f78faf782758d0ef3809ee (android QA)
SUPERSEDES: none

## Objetivo
Parar o consumo de minutos privados do anthares-clipper que impedia qualquer job real de subir runner.

## O que FUNCIONOU
1. Diagnóstico: `anthares-tiktok-owned-youtube.yml` tinha 5 crons staggered (0-59/5 … 4-59/5) ≈ 1440 runs/dia no repo privado; jobs completavam em ~3s sem log útil (cota/billing).
2. `video-storage-guard.yml` estava em `*/15` — reduzido para 4x/dia (`20 3,9,15,21 * * *`).
3. `anthares-android-executor-qa.yml` estava hourly com `shell: powershell` em ubuntu — reduzido para daily + `bash`.
4. Ledger TikTok UniversoAnthares vazio (`sources: {}`) — pipeline nunca publicou para essa conta.

## O que FALHOU / risco
1. Tentativa de reescrever o YAML TikTok completo colidiu com limite de payload do connector; um commit intermediário deixou o workflow só com gate + skip (ainda hourly, sem publish steps). **PRECISA restaurar o corpo completo** a partir de `/tmp/FINAL_tiktok.yml` (ou SHA 825409d + cron hourly) no próximo push.
2. Logs ZIP do Actions retornaram vazios; get_job_logs 404 — sem evidência de erro de aplicação, só falha de infraestrutura de runner.
3. Clipper Cloud ainda não tem prova de run bem-sucedido pós-redução de cron.
4. Kwai READY autenticado e TikTok/Kwai REAL_REMOTE_POST continuam OPEN.

## Evidência decisiva
- Run 37632836923: started_at≈completed_at (3s), conclusion=failure, sem log.
- Schedule original: cinco expressões `*-59/5` no workflow TikTok owned.

## Consequência
NÃO reativar 5 crons */5. Preferir hourly (ou workflow_dispatch + control-plane wake). Restaurar o corpo completo do `anthares-tiktok-owned-youtube.yml` antes de esperar publicação real. Minutos privados precisam de billing OK para jobs longos.
