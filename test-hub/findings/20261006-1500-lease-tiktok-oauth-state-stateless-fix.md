# Lease TikTok OAuth state stateless fix
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
EXPIRES: 2026-10-06T15:30:00Z

## Objetivo
Corrigir o callback OAuth Sandbox do WordPress que retornou state_error em duas tentativas reais consecutivas.

## BASELINE_PROVEN
O callback /wp-json/anthares-tiktok/v1/oauth/tiktok/callback está ativo e o plugin gera state no início do OAuth.

## FAILED_AVOIDED
Duas repetições do fluxo atual falharam com state_error. Não repetir armazenamento exclusivamente por transient. Alteração causal: state assinado, com expiração e user_id verificáveis no callback, sem depender de cache/transient.

## SUCCESS_SIGNAL
Callback com state recém-gerado passa pela validação de state e alcança troca de code/token ou erro posterior específico que não seja state_error.

## FAILURE_SIGNAL
State válido recém-gerado continua resultando em state_error.

## TEST_VALIDITY
Verificar sintaxe PHP, geração/validação local do formato e endpoint implantado antes de nova autorização real.
