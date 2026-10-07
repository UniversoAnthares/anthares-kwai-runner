# Lease cloudflare-control Git provider router
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-07
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

## Objetivo
Integrar a politica peer GitHub/GitLab ao anthares-control, manter escrita fail-closed por checkpoint SHA e preparar sincronizacao GitHub->GitLab sem loop.

## BASELINE_PROVEN
provider_router.py possui estados READY/BLOCKED_QUOTA/DOWN/AUTH_REQUIRED/UNKNOWN/BUSY e bloqueia failover quando o checkpoint diverge. anthares-control existe em anthares-clipper/cloudflare-worker e e o control plane persistente.

## FAILED_AVOIDED
Nao ativar mirror bidirecional cego; nao depender apenas de GitHub Actions; nao inserir tokens/URLs com credenciais no codigo ou Test Hub; nao escrever quando os SHAs divergem.

## SUCCESS_SIGNAL
Testes cobrem GitHub READY, failover para GitLab, retorno GitLab->GitHub, ambos indisponiveis e divergencia SHA bloqueada; control plane recebe politica equivalente e secrets ficam fora do repositorio.

## FAILURE_SIGNAL
Qualquer caso permite escrita com checkpoint divergente, dois provedores simultaneamente ou nenhum provedor READY.

## TEST_VALIDITY
Testes deterministas sem rede validam a politica; integracao real so sera marcada PROVEN apos deploy/teste independente.

## Lease
Expira em 30 minutos.
