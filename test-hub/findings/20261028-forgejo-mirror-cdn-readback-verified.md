# Forgejo: espelho Git independente e verificação CI homologados
STATUS: PROVEN
AREA: architecture/forgejo-git-ci-redundancy
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40746611827
JOB: 123025502074
COMMIT: 523d5e3ff6d527628240ae283e5a715b1214771e
SUPERSEDES: 20261028-lease-architecture-forgejo-sync-cdn-readback.md

## Escopo e causa
A rotina de GitHub Actions conseguia obter o SHA do Forgejo pelo antigo endpoint, mas falhava com HTTP 403 da CDN no comando `git ls-remote`. O endpoint anterior fazia `git fetch --prune` com refspec de sobrescrita. A rotina GitHub→Forgejo independente na Hostinger também falhava ao tentar `git push` pelo Git HTTPS bloqueado pela CDN.

## Correção comprovada
- PR #1800, incorporado ao `main`, atualizou `.github/workflows/forgejo-mirror-sync.yml` e `infra/forgejo-proxy/sync.php`.
- O endpoint HTTP POST na Hostinger é somente leitura. Confere comprovante privado recente, ausência de falhas, `no_force=true`, `no_prune=true` e SHA efetivo de `refs/heads/main`. Falha fechada se qualquer condição não for satisfeita.
- A rotina Hostinger GitHub-only existente passou a importar as referências por `git fetch --atomic --no-tags` de seu espelho verificado para o repositório local do Forgejo, sem `force`, `prune` ou dependência do Git HTTPS da CDN. Backup privado anterior preservado.
- A sincronização Hostinger atualizada confirmou 15 origens, zero falhas e o SHA `523d5e3ff6d527628240ae283e5a715b1214771e` no Kwai Runner.
- O job GitHub Actions #123025502074 (reexecução única após correção causal) terminou SUCCESS e registrou `HOSTINGER_INDEPENDENT_RECEIPT=PROVEN` e `CROSS_PROVIDER_SHA_CHECK=PROVEN sha=523d5e3ff6d527628240ae283e5a715b1214771e`.
- A prova independente Forgejo Actions OIDC #266 foi SUCCESS, com `FORGEJO_OIDC_LIVE_SIGNATURE_AND_SCOPE=PASS`.
- Em recuperação isolada, 13/13 repositórios GitHub não vazios tiveram referências/SHAs/árvores/objetos verificados e 2/2 fontes vazias foram identificadas; sem publicação nem arquivos temporários restantes.

## Limites explícitos
Esta prova homologa a redundância **GitHub→Forgejo e o CI não publicador**. Não comprova failover de publicação social ou recuperação integral de fontes GitLab independentes.

Seis históricos GitLab: 62/180 referências de mesmo nome/hash, 118 divergentes e 95 objetos-tip não presentes no Forgejo; somente 1/6 histórico integral. A escrita desses históricos permanece sujeita à revisão do bloqueio de segurança da ferramenta, não ao ticket CDN da Hostinger. O histórico exclusivo Codeberg Clipper permanece protegido em backup privado, sem fusão com `main`.

X segue com `X_NEON_LEDGER_NOT_RECONCILED`; health do Neon não substitui reconciliação de estado e não autoriza disparo de publicação. Nenhum publicador foi ativado ou executado nesta homologação.

LEASE: ENCERRADO — escopo de alteração do comprovante e workflow concluído.
CONCLUSÃO DO ITEM FIXO 6: PARTIAL, aguardando desbloqueio de históricos GitLab e homologação de execução/publicação.
