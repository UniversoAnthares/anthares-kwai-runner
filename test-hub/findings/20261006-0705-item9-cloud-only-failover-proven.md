# Item 9 — Cloud-only failover definitivo
STATUS: PROVEN
AREA: cloudflare-control
DATE: 2026-10-06
SUPERSEDES: test-hub/findings/20261006-0643-lease-cloudflare-control-failover-item9.md; test-hub/findings/20261006-0659-lease-cloudflare-control-failover-item9-renewal.md

## Resultado
O failover real do control plane está fechado sem dependência operacional do PC. O Worker manteve o contrato de fila/fencing v16 e recebeu a revisão de roteamento `2026-10-06-cloud-only-failover-r1`.

## Código e deploy
- Hardening principal em `68cc5211897701747d0abfb6a52b9320eec9fc81`.
- Deploy executado a partir de `origin/main` descendente contendo esse commit; `cloudflare-worker/src/index.js` foi verificado como inalterado desde `68cc521` antes do deploy.
- Pós-deploy, `/health` retornou `version=2026-10-05-queue-fencing-v16`, `routing_revision=2026-10-06-cloud-only-failover-r1`, `pc_fallback=false`.
- `/strategy` retornou somente rotas cloud: cuts Render->GitHub; TikTok Render->GitHub; Kwai GitHub; Kwai LIVE HLS origin->GitHub; control Cloudflare->GitHub->Render. Oracle e Google Compute permanecem false.

## Matriz de failover em produção
`/failover-self-test` retornou `ok=true` e todos os checks abaixo true:
- `primary_render`
- `render_offline_github`
- `all_cloud_offline_null`
- `stale_heartbeat_github`
- `circuit_breaker_github`
- `capacity_github`
- `readiness_github`
- `recovery_returns_render`
- `cuts_failover`
- `kwai_github_only`
- `kwai_outage_null`
- `live_hls_primary`
- `live_hls_failover`
- `retired_absent_priorities`
- `retired_injected_never_selected`

Sinais observados: primary=`render`; após falha Render=`github`; após falha Render+GitHub=`null`; após recuperação=`render`.

## Estado/lease/falhas
Os contratos já PROVEN de queue-fencing v16 permanecem inalterados: leases e generations, renew, started, UNCERTAIN/reconcile, crash recovery, stale-owner rejection, confirmação e dedupe. O estado de executor continua registrando heartbeat, falhas consecutivas/circuit breaker, `last_success_at`, `last_failure_at`, `published_today` e capacidade; a nova matriz prova explicitamente stale heartbeat, breaker e limite diário como sinais de roteamento.

## Executores aposentados
`RETIRED_EXECUTORS = local, pc, windows, oracle, google, google_compute` é aplicado à autenticação de executor, heartbeat e operações genéricas de job. Prova negativa pós-deploy: POST `/heartbeat` para cada um desses seis IDs retornou HTTP 410. `/job/enqueue-local` também retornou 410.

## Prova independente sem PC
Commit de aceitação pós-deploy: `fbd4061ac63e4fe025b8f6d8e7aaba91e8917b43`.
GitHub Actions `Control Plane Static Safety Validation`, run `37453759746`, job `safety`, executado em `ubuntu-24.04`, conclusão `success`. O job validou fresh checkout + invariantes estáticos + os três endpoints publicados e exigiu todos os checks acima.

## Conclusão
Item 9 fechado. Quando o primário falha o controlador troca somente para executor cloud elegível; quando não existe executor cloud elegível falha fechado; quando o primário retorna ele volta a ser selecionado. Não existe fallback silencioso para o PC, Oracle ou Google Compute.