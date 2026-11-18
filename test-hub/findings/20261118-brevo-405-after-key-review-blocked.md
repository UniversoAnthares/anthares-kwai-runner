# Brevo Anthares Mailing: criação de rascunho recusada após revisão visual de permissões
STATUS: BLOCKED_EXTERNAL
DATE: 2026-11-18
AREA: email
SUPERSEDES: 20261118-brevo-mailing-operator-partial-auth-block.md

## Resultado desta verificação
- Cliente Brevo autenticado via chave dedicada já fornecida pelo titular e armazenada em arquivo 0600 no executor privado Hostinger; sem exposição do segredo.
- Portal Brevo foi observado pelo navegador conectado na aba `app.brevo.com/settings/keys/api/J2anEa/edit`; a interface exibe a chave `Anthares Mailing` com `Campanha de e-mail: Todos`, `Contato: Todos`, `Conta: Lidas` e `Campanhas de WhatsApp: Todos`. O botão `Salvar alterações` estava visível. O estado persistido da edição não pôde ser comprovado pela leitura da aba; o operador não deve presumir que o usuário clicou Salvar.
- Foi realizada uma única nova tentativa controlada de criar o rascunho técnico `anthares-brevo-smoke-20261118v2`, sem qualquer envio. POST `https://api.brevo.com/v3/emailCampaigns` retornou **HTTP 405**, repetindo o bloqueio anterior. Ledger registrou `RECONCILE_REQUIRED` com `brevo_id=null`.
- Uma consulta GET subsequente `/emailCampaigns?status=draft` confirmou `total=0`. O banco local contém dois ensaios técnicos com estado `RECONCILE_REQUIRED`, sem IDs remotos.
- GET `/senders` retornou 200: 1 remetente cadastrado, `contato@anthares.us` presente e ativo. GET `/senders/domains` retornou 200: domínio `anthares.us` presente.
- GET `/account` retornou plano `free`, `credits=300` com tipo `sendLimit`. O limite restringe envio diário, e o plano Free é documentado como elegível à criação de campanhas.
- OPTIONS `/emailCampaigns` retornou 204, HEAD 200. Nenhum deles relata `Allow` com métodos. Essas consultas não permitem deduzir a causa do 405.
- Webhook marketing segue sem permissão (GET retornou 403 antes). O módulo consulta supressões e listas diretamente, e a sincronização foi homologada com um contato e zero bloqueios, sob execução manual.
- Nenhum contato da lista de pastores foi importado. Nenhum e-mail de marketing foi enviado.

## Ação necessária para desbloquear
1. Confirmar se o titular clicou em `Salvar alterações` na tela da chave Brevo. A exibição de permissões selecionadas dentro do editor não comprova persistência.
2. Se a chave já estiver efetivamente salva com `Campanha de e-mail: Todos`, encaminhar ao suporte Brevo os fatos: chave restrita com permissão Total para campanhas, API GET 200 e POST /v3/emailCampaigns 405, plano Free, domínio e remetente ativos. Solicitar causa específica do bloqueio; informar só sufixo da chave se solicitado em canal seguro.
3. Após confirmação externa da correção, reconciliar primeiro os ensaios locais; criar novo rascunho técnico uma única vez, enviar teste exclusivamente para caixa controlada e verificar recebimento.
4. Separar aprovação explícita do conteúdo e da lista antes de qualquer disparo para pastores; manter `BREVO_LIVE_SEND_ENABLED=0` e contato sync desligado.

## Código
- PR draft `#2656` contém adaptador, ledger SQLite, diagnóstico seguro, reconciliação de supressões e operador CLI privado.
- Instalação Hostinger segura na release `658c1f522a6b441516e772257d16f680f40cec24`, 42 testes Brevo + 9 regressões homologados no GitHub Actions `44378937748`.
- Não promover para produção o fluxo de campanhas enquanto houver bloqueio 405.
