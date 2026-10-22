# Redundância independente do Codeberg / Forgejo Actions

Este pacote provisiona um runner de **escopo exclusivo** do repositório `UniversoAnthares/anthares-kwai-runner`. Ele não depende de runners públicos do Codeberg, GitHub Actions ou GitLab para executar jobs depois de iniciado.

**Destino obrigatório:** uma VM Linux dedicada, com Docker Engine e Compose. **Não executar na estação Windows pessoal**, sem isolamento apropriado. O daemon Docker separado (`docker:dind`) não expõe a porta 2375 ao host e isola os containers dos jobs do Docker do host. Ainda assim, a VM deve ser dedicada ao runner porque a execução de código de CI é privilegiada.

A instalação cria apenas um runner de nome `anthares-codeberg-linux-01`, rótulo `anthares-codeberg-linux` e capacidade 1. As credenciais ficam exclusivamente no `data/runner-config.yml` da VM, com permissões restritas. Nenhum token deve ser enviado ao GitHub ou ao ChatGPT.

## Instalação na VM

1. Instale Docker Engine, o plugin Docker Compose e Python 3. Copie esta pasta para a VM.
2. Crie no Codeberg um token com privilégios de administração dos runners do repositório, ou use token administrativo temporário autenticado.
3. Execute `sudo -i`, `cd /caminho/codeberg-independent-forgejo`, depois `read -rsp 'Codeberg API token: ' CODEBERG_ADMIN_TOKEN; echo; export CODEBERG_ADMIN_TOKEN`; por fim, `bash install.sh`.
4. Verifique `docker compose -f compose.yml ps` e confirme o runner online em `https://codeberg.org/UniversoAnthares/anthares-kwai-runner/settings/actions/runners`. Execute manualmente `Codeberg independent Forgejo runner smoke` e exija `CODEBERG_INDEPENDENT_RUNNER_SMOKE=PASS`.

Depois do smoke, despache o workflow `CORTES TikTok lucas4 Codeberg independent runner` com `smoke=true` e `publish=false` para verificar conta/OIDC sem postagem. Só então, e após uma publicação real reconciliada com o Neon, a variável `TIKTOK_CODEBERG_SELFHOSTED_ENABLED=true` poderá habilitar o agendamento independente quando `TIKTOK_CODEBERG_PRIMARY=true`.

O caminho existente `codeberg-medium` e os publicadores GitHub permanecem inalterados até validação. Cada trabalho de publicação usa o mesmo ledger/lease de proteção do Neon; nunca republicar IDs em estados `started`, `uncertain` ou `closed_unverified`.

**Evidências obrigatórias:** runner online pela API do Codeberg, smoke bem-sucedido, teste OIDC com identidade exata e link remoto de nova publicação igual ao `remote_id` com status `confirmed` no Neon. Sem essas provas, não promover a prioridade.
