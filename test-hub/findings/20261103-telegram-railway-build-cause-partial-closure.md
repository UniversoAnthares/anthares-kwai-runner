# Railway Telegram relay — build fatal localizado e correção staged
STATUS: PARTIAL
AREA: telegram-relay
DATE: 2026-11-03
RUN: Railway failed deployment d3cee31d-5731-4589-a869-4b8f5bf3748e
JOB: https://github.com/UniversoAnthares/anthares-telegram-relay/pull/5
COMMIT: 6bca62a611e1b1a18c4f7f0abf5e300e11a8ec2a
SUPERSEDES: test-hub/findings/20261103-telegram-railway-dockerfile-lease.md

## Evidência decisiva
Railway projeto accurate-commitment / anthares-telegram-relay com 6 variáveis, domínio anthares-telegram-relay-production.up.railway.app e volume persistente montado em /var/lib/anthares-telegram-relay. Última implantação FAILED; build log: "dockerfile invalid: docker VOLUME at Line 15 is not supported, use Railway Volumes". Projeto worthy-heart também FAILED e não tem domínio/variáveis/volume. Dockerfile no branch da PR #5 remove a diretiva VOLUME, mantendo o volume configurado na Railway intacto.

## Resultado e pendências
Correção no código, ainda sem build/redeploy/teste live. PR #5 contém também correção de idempotência e normalização de erros do relay, sem testes completos. Há risco de UID/permissão no volume montado; verificar depois de build. Conta Railway não expõe a comprovação de custo zero nesta sessão, e dois projetos acompanham a mesma source repo; evitar merge que dispare dois deploys cobrados até reconciliar custos/autodeploy. Nenhuma alteração em runtime, volume, segredos ou publicações. Lease encerrado.
