# Sender.net — integração inicial do mailing Anthares

Status em 18/11/2026: **código e staging PROVEN; autenticação real PENDENTE**.
Esta implementação é uma contingência ao bloqueio de criação de rascunhos no Brevo.
O pipeline geral e a arquitetura principal estão descritos em `docs/email-delivery-architecture.md`.

## Implementado
- `sender_marketing.py` usa **Sender API v2 de marketing**, Bearer token, com `GET /groups`, `GET /campaigns`, `GET /campaigns/{id}` e `GET /groups/{id}/subscribers?page=N`. Os métodos de escrita são `POST /campaigns` (rascunho) e `POST /campaigns/{id}/send`, **ambos desligados por padrão**.
- `SenderDraft` valida remetente, grupo único, assunto e HTML com `{$unsubscribe_link}`. O adaptador desativa acompanhamento automático (`auto_followup_active=false`) e restringe o público a um grupo sem segmentos.
- `sender_campaign_ledger.py`: SQLite privado, identidade local e hash de conteúdo, criação remota com registro prévio, estados `STAGED`, `CREATING`, `REMOTE_DRAFT`, `DISPATCHING`, `RECONCILE_REQUIRED` e `SENT_PENDING_REPORT`. Uma resposta de estado incerto **jamais é repetida automaticamente**.
- O envio requer **aprovações independentes** de conteúdo e destinatários, hashes do conteúdo remoto e da composição da audiência, conferência de `DRAFT` e um `suppression_lookup` global. Um nome de aprovador registrado manualmente ainda não demonstra autenticação; o painel de autorização auditável precisa ser desenvolvido antes da produção.
- `sender_readonly_check.py`: ferramenta de verificação GET-only, sem dados sensíveis na saída. Rejeita arquivos de token com permissões abertas, ou quando os switches de escrita estão habilitados.
- `tests/test_sender_marketing.py` e `tests/test_sender_readonly_check.py`: testes de contratos sem credenciais reais nem envio.

## Evidência de homologação
- GitHub Actions [Sender marketing contracts (offline), run 44394247824](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44394247824): **27 testes Sender aprovados** e **9 testes existentes do sistema de e-mail aprovados**.
- Staging Hostinger: release privada e imutável `52f5889efc95fa94ee5575bb8f4ce75d42ec97a0`, instalada em `/home/u566597497/.anthares-sender-mailer/current`, fora do `public_html`. Hash do arquivo `sender_readonly_check.py` verificado: `21285563345ace089aa648ec22dedd15cedbf2a7`. Os **27 testes** Sender também passaram no Python 3.11 do servidor.
- `/home/u566597497/.anthares-sender-mailer/state/sender_campaigns.sqlite3` criado, **zero campanhas**, modo `0600`.
- Pasta de token preparada no gerenciador Hostinger: `/home/u566597497/domains/anthares.us/anthares-sender-mailer/sender-api-token.txt`. Acesso somente ao proprietário (`0600`), fora do diretório público, linked ao `state` privado.
- **O arquivo do token está vazio (0 bytes)**. Nenhuma conta Sender já autenticada foi identificada nas abas do navegador, no ambiente do processo remoto ou nas mensagens de cadastro pesquisadas nas caixas vinculadas. Nenhuma requisição autenticada ao Sender ocorreu nesta etapa.
- Brevo, WordPress, serviço de e-mail e DNS atual do domínio **não foram modificados**.

## A única etapa manual de autenticação
1. Criar/acessar conta em [Sender](https://www.sender.net/), preferencialmente cadastrada com `contato@anthares.us` e nome da organização `Universo Anthares`.
2. Verificar a conta e o remetente, acessar **Account settings → Domains** e cadastrar `anthares.us`, seguindo as instruções de verificação do provedor. Não substituir registros MX Hostinger; antes de alterar SPF/DKIM, verificar o estado atual para preservar autenticação dos demais provedores.
3. Em **Account settings → API access tokens → Create API token**, criar um token dedicado ao Anthares Mailing. O fornecedor oferece validade **Forever, 30 dias, 7 dias, 1 dia**; preferir prazo apropriado à operação e registrar a data da próxima rotação.
4. **Guardar o token diretamente no arquivo privado Hostinger**, nunca em chat, GitHub ou email:
   `domains/anthares.us/anthares-sender-mailer/sender-api-token.txt`.
5. Após o titular confirmar que salvou o token, rodar o diagnóstico existente:
   `cd /home/u566597497/.anthares-sender-mailer/current && env SENDER_DRAFT_WRITE_ENABLED=0 SENDER_LIVE_SEND_ENABLED=0 /opt/alt/python311/bin/python3.11 sender_readonly_check.py --token-file /home/u566597497/.anthares-sender-mailer/state/sender-api-token.txt`.
   O resultado deve ser `authenticated=true`, `groups=ok`, `campaign_drafts=ok`, `dispatch=disabled`, sem exibir dados privados.

## Etapas posteriores
- Com autenticação real confirmada: cadastrar/verificar domínio e remetente, criar um **grupo de teste com controle do titular**; não migrar destinatários históricos sem origem e base de contato válida.
- Autorizar explicitamente criação de **um único rascunho técnico**; reconciliar respostas incertas; testar exclusivamente a caixa controlada.
- Integrar registros de descadastro e reclamações com a base global de supressões. A API do Sender permite consulta por assinante/grupo e por campanha; webhooks de conta são indicados como recurso pago na documentação.
- Integrar aprovação autenticada e auditável na interface do Anthares antes de permitir `SENDER_LIVE_SEND_ENABLED=1`.
- Conferir limites reais do plano. A oferta oficial Free informa **2.500 assinantes** e **15.000 envios/mês**, com marca Sender no rodapé. Uma audiência mais numerosa pode exigir plano pago.
- Consultar a resposta do suporte Brevo antes de decidir o desligamento definitivo. Evitar disparos duplicados entre provedores.

## Documentação oficial consultada
- API criar campanha: https://api.sender.net/campaigns/create-campaign/
- API enviar campanha: https://api.sender.net/campaigns/send/
- API assinantes por grupo: https://api.sender.net/groups/subscribers/
- API listar campanhas: https://api.sender.net/campaigns/get-all/
- Autenticação e tokens: https://www.sender.net/help/ecommerce-and-integrations/rest-api-authentication/
- Verificação da conta: https://www.sender.net/help/account-settings-and-billing/account-verification-process/
- Plano Free: https://www.sender.net/pricing/free-plan/
