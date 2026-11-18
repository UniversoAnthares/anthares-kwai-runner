# Anthares Mailing — contingência de provedores (18/11/2026)

Status: levantamento documentado, **nenhuma migração ou envio autorizado**. Referência principal: `docs/email-delivery-architecture.md`.

## Solicitação enviada à Brevo
- Em 18/11/2026, `contato@anthares.us` enviou solicitação para `contact@brevo.com` pela caixa Hostinger. A API de envio Hostinger retornou HTTP 204 e a mensagem foi confirmada na pasta `INBOX.Sent`, UID 8.
- Assunto: `Suporte técnico Brevo — POST /v3/emailCampaigns retorna HTTP 405 (anthares.us)`.
- A solicitação informa falhas repetidas de POST `/v3/emailCampaigns` com 405, GET de conta/listas/campanhas com 200, remetente e domínio validados, plano Free e permissões de chave observadas; solicita identificação de bloqueios específicos de conta e autorização de webhooks (GET 403). Não inclui segredos.
- Acompanhamento: procurar resposta da Brevo na caixa `contato@anthares.us` usando o assunto acima, responder na mesma conversa e registrar o número do chamado quando houver. Nenhum SLA foi assumido.

## Alternativas verificadas em documentação do fornecedor

| Provedor | Campanhas pela API | Plano gratuito divulgado em novembro de 2026 | Compatibilidade |
|---|---|---|---|
| **Sender.net** | `POST https://api.sender.net/v2/campaigns` cria rascunho; `POST /v2/campaigns/{id}/send` envia após autorização. Bearer token e criação de conta necessários. | 2.500 assinantes, 15.000 envios/mês; acesso à API no plano Free | **Primeira alternativa para piloto**. Capacidade de marketing, segmentação, descadastramento, API e domínio próprio. |
| **Resend Broadcasts** | API `/broadcasts` cria, agenda e envia campanhas; a plataforma gerencia o descadastro quando o placeholder oficial é usado. | Free marketing divulgado com até 1.000 contatos, envios de Broadcast cobrados pela faixa de contatos; revisar preço vivo antes de contratar. | **Segunda alternativa técnica** e já prevista na arquitetura, exigindo conexão real e confirmação de domínio. |
| **Mailjet** | API `/v3/REST/campaigndraft` cria campanha, seguida de etapas de conteúdo, teste e envio. | Free: 1.000 contatos totais, 6.000 mensagens/mês, 200/dia e limite de 200 destinatários por campanha pelo editor. | Alternativa estável com API, porém menor alcance gratuito. |
| **MailerLite** | Plataforma de marketing com API e campanhas, elegibilidade de API conforme plano deve ser verificada. | Free: até 250 assinantes e 2.500 envios em 30 dias. | Limite gratuito insuficiente para mailing amplo. |
| **SendPulse** | Plataforma de marketing e SMTP/API. | Free até 500 assinantes; volumes publicados variam por produto. | Menor prioridade para este projeto. |

## Links oficiais consultados
- Sender API criar campanha: https://api.sender.net/campaigns/create-campaign/
- Sender API enviar: https://api.sender.net/campaigns/send/
- Sender Free: https://www.sender.net/pricing/free-plan/
- Resend Broadcasts: https://resend.com/changelog/create-and-send-broadcasts-via-api
- Resend marketing: https://resend.com/products/marketing-emails
- Resend preços: https://resend.com/pricing
- Mailjet criar draft: https://dev.mailjet.com/docs/email-api/send-campaign-draft/create-campaign-draft
- Mailjet limites Free: https://documentation.mailjet.com/hc/en-us/articles/19154256993051-Understanding-Mailjet-Free-Plan-Limits
- MailerLite Free: https://www.mailerlite.com/help/free-plan-update-faq
- SendPulse preços: https://sendpulse.com/pricing

## Integração e estratégia

1. Manter o módulo de fila, ledger, supressões e gates de dupla aprovação independente de provedor.
2. Implementar adaptador **Sender** em branch isolada após decisão e autorização de criação/conexão de conta. Testes mock sem transmissão real ou importação de destinatários.
3. Antes de qualquer teste real: cadastrar domínio no novo provedor, validar DNS SPF/DKIM/DMARC sem interromper MX Hostinger, registrar remetente, obter token em cofre privado e verificar GET.
4. Usar `contato@anthares.us` para recebimento de respostas. Separar marketing e e-mail transacional; seguir políticas do provedor e aplicar descadastro em todas as plataformas.
5. Identificar origem, consentimento, finalidade e evidência de autorização de cada contato. Endereços públicos em diretórios não constituem prova de consentimento. Evitar duplicação de envios entre Brevo/Sender/Resend.
6. O custo de ampliar cada alternativa para milhares de destinatários depende do total *real* de pessoas qualificadas, frequência e cadência de envios; nenhum número de destinatários foi aprovado.
7. **Bloqueios permanentes:** não promover reenvio de marketing via APIs transacionais apenas para contornar o 405; não duplicar campanha automaticamente após timeout; não enviar sem aceite de conteúdo e público.

## Estado de execução
- Suporte Brevo: solicitação enviada e confirmada em Enviados; resposta e número de chamado ainda desconhecidos.
- Pesquisa comparativa: concluída e documentada.
- Migração: nenhuma; contas Sender/Resend/Mailjet não foram conectadas por esta tarefa.
- Produção: Brevo permanece com leitura API autenticada e envio de campanha desativado.
