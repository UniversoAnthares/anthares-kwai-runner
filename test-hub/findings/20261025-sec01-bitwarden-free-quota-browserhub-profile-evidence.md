# SEC-01 (item fixo 06) — inventário Bitwarden Free e Browser Hub — 2026-10-25

Estado: **PARTIAL**. Evidências de leitura administrativa, inventário de plano e recuperação do perfil de navegador. Este finding é **append-only** e complementa `20261025-sec01-threads-bws-metadata-proven-scope-partial.md`, sem substituir as provas anteriores.

## Identidade e assinatura (leitura autenticada sem extração de valores)

- Organização: Anthares Secrets.
- Admin Console → Faturamento → Assinatura em `https://vault.bitwarden.com/#/organizations/78a2d0d1-e41e-4250-a95c-b4e800e1d783/billing/subscription`: Password Manager organização gratuita (Grátis) e Secrets Manager organização gratuita (Grátis).
- Informação explícita da assinatura: não é possível convidar mais de 2 usuários sem upgrade; armazenamento de anexos 0 GB contratado e 0 MB usado.
- Secrets Manager: 3 projetos (Anthares AI, Anthares Automation, Anthares Core), 8 segredos, 3 contas de máquina (`anthares-ai`, `anthares-automation`, `anthares-core`).
- Distribuição dos 8 segredos: 7 no projeto Anthares Automation e 1 no Anthares AI.
- O número de segredos associados a contas de máquina (1/7/1) não comprova exclusividade de projeto nem permissões de leitura/gravação. Não inferir autorização de escrita.
- Limites publicados pelo fornecedor para Secrets Manager Free: até 3 projetos, 3 contas de máquina, 2 usuários e segredos ilimitados. Fontes: https://bitwarden.com/en-gb/help/secrets-manager-faqs/ e https://bitwarden.com/help/machine-accounts/. Capacidade restante pela comparação com o inventário: 0 projetos e 0 contas de máquina, sem compra ou upgrade.

## Controle da sessão e Browser Hub

- O Chrome pessoal já autenticado no Bitwarden permaneceu intacto. O conector Anthares Browser leu somente textos/metadados de abas; nenhuma senha/token/cookie foi exposto.
- O perfil isolado `D:\AntharsWork\browser-profiles\AntharesBitwardenAdmin` foi registrado em `AntharesBrowserHub.ps1` com porta **0 (CDP desativado)** para não disponibilizar um cofre administrativo à automação genérica. `resolve` aponta para o diretório e `health` reporta `exists=true`, `running=false`, `port=0`, `cdp=false`.
- O processo órfão `chrome.exe` PID 14968, iniciado anteriormente por este job no Windows Session 0, foi encerrado com sua árvore após checagem de proprietário e perfil. Contagem posterior do perfil: 0 processos. Chrome pessoal PID 20524 preservado.
- Teste headless de Chrome com `--user-data-dir` isolado, `--dump-dom=about:blank`: **exit 0**, 0 processos residuais. Isso comprova inicialização local do perfil, **não** autenticação administrativa do perfil isolado.
- Backup pré-mudança `AntharesBrowserHub.ps1.sec01-20261025.bak`. SHA256 do script alterado: `1D0332C55643ADA76B79DB7646AC6A71A4E19A2049DDEE43D8953103E0798A89`.
- README local atualizado com nota SEC-01 e backup próprio. A tentativa de restringir ACL de 2.505 arquivos não foi aceita integralmente; **ACL anterior restaurada integralmente (2.505 de 2.505, zero falhas)**. Endurecimento do perfil está **pendente**, e o perfil isolado não deve receber autenticação administrativa até essa pendência ser resolvida. Nenhum outro perfil foi alterado.

## Teste de token já realizado

- PR draft #1399 e GitHub Actions run 40235027169: SDK do Bitwarden autenticou com `BWS_ACCESS_TOKEN`, leu **somente metadados** do segredo Threads e comprovou `Anthares Automation` como projeto, sem revelar segredo.
- Este teste **não identifica a conta emissora do token**, não atesta permissão de escrita, não prova isolamento negativo de todos os projetos e não autentica o Chrome isolado.

## Critérios pendentes (não declarar item concluído)

1. Obter evidência administrativa de projetos, permissões de leitura/gravação e tokens **metadados** por conta de máquina, sem revelar valores.
2. Correlacionar a conta de máquina emissora do `BWS_ACCESS_TOKEN` no GitHub com registro administrativo; não presumir que nomes de conta/projeto coincidam.
3. Endurecer ACL de perfil admin com procedimento seguro, revalidar sessão isolada sem transferir cookies e confirmar persistência/autenticação por ação legítima do titular, se requerida.
4. Reconciliar a divergência do manifesto local `f6fc9ca59a96e451` vs GitHub main `2e28d54043d6bad1`, antes de declarar sincronização canônica.

Sem upgrade, alterações de IAM/credenciais, consumo de segredos, alterações de filas, publicações ou deploys.
