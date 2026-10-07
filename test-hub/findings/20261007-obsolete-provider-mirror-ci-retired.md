# Obsolete provider-specific mirror CI retired
STATUS: PROVEN
AREA: architecture/provider-sync
DATE: 2026-10-07
RUN: post-activation cleanup
JOB: manual maintenance
COMMIT: d0e7db012b54e6ef2b83075db6057ff14c478687
SUPERSEDES: 20261007-1758-git-provider-automatic-sync-enabled.md

## Objetivo
Remover os mecanismos antigos de sincronização que dependiam de GitHub Actions privado ou de variáveis de mirror não configuradas, agora que o Anthares Git Mirror externo está ativo.

## Alterações
- Removido `.github/workflows/gitlab-mirror-sync.yml` de `anthares-kwai-runner`.
- Removido `.gitlab-ci.yml` de `anthares-kwai-runner`.
- Nenhum histórico foi reescrito e nenhum force-push foi usado.

## Motivo
O workflow antigo do GitHub dependia de `GITLAB_MIRROR_URL` e o CI antigo do GitLab dependia de `GITHUB_MIRROR_URL`. O pipeline GitLab 2924184018 falhou imediatamente por essa configuração ausente. Esses mecanismos são redundantes e conflitantes com o Anthares Git Mirror, que agora é o transporte de sincronização entre os dois provedores.

## Resultado
A sincronização passa a ter um único mecanismo externo de transporte, mantendo GitHub e GitLab como pares. Os mecanismos antigos não podem mais disparar uma segunda sincronização ou produzir falsos failures de CI.

## Segurança
A política fail-closed, com bloqueio de divergência bilateral, permanece a proteção contra sobrescrita indevida.
