# Anthares control GitHub/GitLab reconciliation
STATUS: PROVEN
AREA: architecture/cloudflare-control
DATE: 2026-10-07
RUN: provider parity repair
JOB: anthares-control source reconciliation
COMMIT: GitHub cdb82e4d0069471f553b73a46c97d0998b206d2d; GitLab bf4cb9e72faf764d492f1df63cb09652fd4eabdf
SUPERSEDES: none

## Resultado
O `anthares-control` no GitHub já continha a integração `git-provider-router.js`, enquanto o espelho GitLab ainda não havia recebido essa atualização.

A entrada `cloudflare-worker/src/index.js` e o módulo `cloudflare-worker/src/git-provider-router.js` foram reconciliados no GitLab sem reescrever histórico e sem force-push.

## Política preservada
- GitHub e GitLab permanecem pares.
- Failover só ocorre quando o provedor atual está indisponível.
- O alvo precisa estar READY.
- O checkpoint precisa permanecer no mesmo commit.
- Divergência bloqueia a operação.

## Verificação
O GitLab agora contém o módulo `git-provider-router.js` e o entrypoint contém a importação correspondente.
