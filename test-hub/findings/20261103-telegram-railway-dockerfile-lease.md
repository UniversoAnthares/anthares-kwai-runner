# Reparo Telegram Railway — build Dockerfile
STATUS: RUNNING
AREA: telegram-relay
DATE: 2026-11-03
RUN: Railway deployment d3cee31d-5731-4589-a869-4b8f5bf3748e
JOB: Telegram relay PR #5
COMMIT: 39432448ce52490b55d93648bd320c05f5306a9c
SUPERSEDES: none

## Baseline
Railway projeto accurate-commitment, serviço anthares-telegram-relay, produção. Build FAIL por “dockerfile invalid: docker VOLUME at Line 15 is not supported, use Railway Volumes”; há volume persistente montado em /var/lib/anthares-telegram-relay, variáveis configuradas e domínio anthares-telegram-relay-production.up.railway.app. Projeto duplicado worthy-heart sem domínio, variáveis ou volume. Ambos FAILED no build. Repo GitHub main Dockerfile SHA 8c53119664b410f2b35b6a52e625d8bef0fc818a; branch fix/relay-send-idempotency-20261103 HEAD 39432448ce52490b55d93648bd320c05f5306a9c. Peer GitLab consultado sem promover.

## Objetivo
Corrigir a causa específica no Dockerfile existente, preservando o volume e outras variáveis. Nenhum serviço/volume/recurso novo e nenhum custo novo. Rodar validação sintática; eventual deploy só se demonstrar compatibilidade com custo zero e com as condições de QA do projeto.

## FAILED_AVOIDED
Não repetir a tentativa de deploy anterior sem remover VOLUME. Não recriar sessão, conexão, segredo ou volume. Não editar projeto duplicado. Não enviar mensagem Telegram real de teste.

## SUCCESS_SIGNAL
Dockerfile limpo de VOLUME; teste de build e health da aplicação em ambiente autorizado, com status ainda condicionado a deploy.

## FAILURE_SIGNAL
Build falha por mesma instrução; perda de dados persistentes, custo, regressão na inicialização.

## TEST_VALIDITY
Teste somente de repositório comprova correção do arquivo; real acceptance demanda health Railway + callback + sessão autorizada.

## Lease
telegram-relay por 30 min, restrito a Dockerfile na PR #5. Encerrar com novo finding.
