# Git redundancy alternates — Forgejo operational, GitLab auth remains
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37472958434
JOB: 112300943402
COMMIT: 3f19300f37341597c5ce1967e1fd1caea5f101c1
SUPERSEDES: 20261006-0900-git-provider-redundancy-auth-boundary.md

## Objetivo
Fechar redundância fora do GitHub por caminhos independentes da autorização inicial.

## Resultado
PROVEN: Forgejo 15.0.9 autohospedado no Hostinger, persistente fora do PC, com SQLite e repositório mirror.
PROVEN: HTTPS público em https://anthares.us/forgejo/ via proxy PHP isolado para socket Unix; /api/v1/version retorna 200 e git ls-remote funciona.
PROVEN: GitHub→Forgejo sincroniza por endpoint fixo sem parâmetros externos; run 37472958434 terminou success e emitiu SYNC_PROVEN e CROSS_PROVIDER_SHA_CHECK=PROVEN no SHA 3f19300f37341597c5ce1967e1fd1caea5f101c1.
PROVEN: clone/ls-remote externo do Forgejo retorna o mesmo main SHA do GitHub após sync.
PROVEN: workflow forgejo-mirror-sync.yml agenda convergência a cada 10 minutos sem depender do PC.
PARTIAL: acesso de agente ao Forgejo possui API pública e MCP Forgejo compatível identificado; escrita via MCP ainda precisa ser ligada a credencial dedicada sem expor token.
PARTIAL: GitLab público UniversoAnthares existe. SSH atual falhou com Permission denied (publickey); não repetir sem nova chave/credencial. MCP oficial GitLab está configurado no Codex e OAuth foi reiniciado; aguarda aprovação da sessão.
FAILED/AVOIDED: GitHub Actions do anthares-wordpress não pode ser usado como executor de bootstrap neste momento; run 37471258845 foi bloqueado antes do job por billing/spending limit. Não repetir até mudança causal.
FAILED/AVOIDED: Cloudflare Quick Tunnel sobre Hostinger não é a rota escolhida; UDP/QUIC é bloqueado e quick-tunnel --url tratou Unix socket incorretamente. O proxy PHP/Unix já substitui essa rota.

## Evidência decisiva
Run 37472958434/job 112300943402: success; SYNC_PROVEN 3f19300f37341597c5ce1967e1fd1caea5f101c1; CROSS_PROVIDER_SHA_CHECK=PROVEN no mesmo SHA.
Teste externo: git ls-remote https://anthares.us/forgejo/anthares-admin/anthares-kwai-runner.git refs/heads/main retornou o mesmo SHA.
GitLab SSH probe job 357dc2b53082e593: Permission denied (publickey).
Private Actions bootstrap run 37471258845: job não iniciou por billing/spending limit.

## Consequência
Preservar o Forgejo atual e o proxy /forgejo/. Próximo agente deve priorizar: (1) concluir OAuth GitLab e criar/importar mirror; (2) instalar Forgejo MCP com credencial dedicada e testar branch+commit; (3) expandir mirrors somente depois do primeiro repositório permanecer estável. Não usar Quick Tunnel nem private Actions até mudança causal.

## Lease closure
Lease 20261006-0925-lease-architecture-git-redundancy-alternates.md encerrado por esta evidência.
