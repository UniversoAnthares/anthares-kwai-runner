# Lease — social auth/browser final closure
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: social-auth-browser-final
COMMIT: none
SUPERSEDES: none

## Objetivo
Fechar os gates reais de Instagram/Threads e X, reutilizando autorização/sessões existentes e criando rota browser gratuita quando necessário.

## BASELINE_PROVEN
20261006-1335-social-direct-adapters-contract-partial.md: contratos dos adaptadores diretos passaram; destination_key e confirmação fail-closed preservados.

## FAILED_AVOIDED
Não habilitar X API paga implicitamente. Não extrair/expor cookies, senhas ou tokens. Não considerar navegador aberto como autenticação comprovada. Não concluir delivery sem evidência remota.

## SUCCESS_SIGNAL
Sessão/autorização legítima identificada e canário real confirmado por destino, ou gate reduzido a uma ação de consentimento inevitável com toda infraestrutura pronta.

## FAILURE_SIGNAL
Sessão inexistente/expirada, consentimento interativo obrigatório ou plataforma bloqueando automação sem mecanismo autorizado.

## TEST_VALIDITY
Probes de sessão são somente-leitura até haver lease; canário deve produzir remote_id/URL ou evidência independente equivalente.

## Expiração
2026-10-06T14:08:00Z.
