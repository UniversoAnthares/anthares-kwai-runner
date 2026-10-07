# Manual actions + private Actions quota blocker
STATUS: PARTIAL
AREA: github
DATE: 2026-10-07
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/37643865796
COMMIT: 7a472884f6793f608d4a62976b3f5e4c62002b9d
SUPERSEDES: 20261007-clipper-actions-minute-burn-fix.md

## Objetivo
Parar queima de minutos privados e listar o que o humano precisa fazer para o pipeline YouTube→cortes→TikTok/Kwai voltar a executar.

## O que FUNCIONOU (código / schedules)
1. TikTok owned workflow no main está **completo de novo** (cron horário `0 * * * *`, steps de prepare/publish/Kwai enqueue presentes). SHA recente `7403da79` / validação `37643865796`.
2. `video-storage-guard` → 4×/dia (não mais */15).
3. `anthares-android-executor-qa` → 1×/dia + shell bash.
4. `anthares-static-hls-validation` → **hourly** (era */5; commit `7a472884`).
5. Control plane Cloudflare `/health` OK: `version=2026-10-05-queue-fencing-v16`, `pc_fallback=false`.

## O que FALHOU / continua bloqueado
1. Jobs no repo **privado** `anthares-clipper` ainda falham sem log útil (ZIP de logs vazio; get_job_logs HTTP 404). Sintoma clássico de **minutos Actions esgotados / billing** no privado — não de bug de Python no clipper.
2. Ledger TikTok UniversoAnthares continua vazio (`sources: {}`) → zero posts registrados nesse caminho.
3. Kwai READY autenticado e REAL_REMOTE_POST (TikTok/Kwai) continuam OPEN.
4. `/queue-health` público retorna unauthorized (esperado; exige OIDC).

## Ação MANUAL obrigatória (humano)
1. **GitHub → Settings → Billing / Plans and usage** da conta UniversoAnthares:
   - Conferir minutos restantes de Actions em repositórios **privados**.
   - Se zero: comprar minutos, ativar spending limit, ou mover o pipeline crítico para o repo **público** `anthares-kwai-runner` (minutos públicos gratuitos).
2. Após ter minutos: disparar manualmente
   - `Anthares TikTok Owned YouTube Cuts` (workflow_dispatch)
   - `Anthares Clipper` (workflow_dispatch)
   e abrir o log do job (não deve mais morrer em 3s sem runner).
3. Confirmar secrets no privado ainda válidos: `TIKTOK_STORAGE_STATE`, `WP_*`, `YOUTUBE_COOKIES`, `RENDER_WORKER_URL`, FTP se usado.
4. Kwai: login autenticado ainda exige superfície de auth após MAIN anônimo (clear-data PROVEN); credenciais/OTP só o humano controla se o app exigir.

## Consequência
Sem minutos privados, nenhum agente consegue provar post real TikTok/Clipper neste repo. Código e schedules já foram reduzidos; o próximo passo causal é **billing/minutos** ou **migrar execução para público**.
