# Integração Brevo Marketing — etapa inicial (18/11/2026)

## Objetivo
Reutilizar a infraestrutura existente Anthares para **campanhas de marketing** no Brevo sem utilizar SMTP transacional nem o Gmail para mailing. O sistema atual WordPress/WP Mail SMTP/Hostinger continua independente.

## Implementado nesta branch
- `brevo_marketing.py`: API v3 de listas, relatórios, rascunhos, sincronização restrita de contatos, teste allowlisted e envio com dupla aprovação.
- `brevo_campaign_ledger.py`: ledger SQLite transacional, identificação local única, marcação `CREATING`, `REMOTE_DRAFT`, `DISPATCHING`, `SCHEDULED` e `RECONCILE_REQUIRED`.
- `tests/test_brevo_marketing.py`: testes offline com transporte falso, sem credencial, sem requisição real e sem destinatários verdadeiros.
- Workflow `brevo-marketing-contracts.yml`: QA seguro em branch/PR.

## Segurança (configuração padrão)
Todas as opções de escrita ficam **desligadas** por padrão:
- `BREVO_DRAFT_WRITE_ENABLED=0`
- `BREVO_CONTACT_SYNC_ENABLED=0`
- `BREVO_TEST_SEND_ENABLED=0`
- `BREVO_LIVE_SEND_ENABLED=0`

`BREVO_API_KEY` deve vir de um cofre/secret autorizado no **executor externo**, nunca do código. A chave WP Mail SMTP comprovada no WordPress não é automaticamente acessível neste executor. Não é permitido copiar segredos de plugins para o repositório.

`BREVO_TEST_RECIPIENT` deve conter um único endereço aprovado para testes; o método `send_test` bloqueia outros destinatários. A rotina nunca envia a uma test-list implícita ou vazia.

## Fluxo de produção futuro
1. Validar a origem, finalidade e autorização de cada contato, deduplicar e consultar recusas anteriores.
2. Persistir contatos e supressões no backend autorizado e sincronizar apenas contatos qualificados com a lista Brevo. A existência de um endereço público não prova consentimento.
3. Preparar a mensagem final, incluindo `{{ unsubscribe }}` e conferir remetente, nome, assunto, HTML e lista.
4. Registrar no ledger, criar somente um rascunho remoto quando habilitado, conferi-lo na Brevo, obter os dois aceites explícitos (campanha e lista de destinatários).
5. Só depois habilitar pontualmente o switch de envio, usar o ledger para despachar uma vez e reconciliar o resultado no Brevo; desligar o switch imediatamente.
6. Implementar sincronização de eventos (descadastramentos, bounces, reclamações) e integração à interface administrativa antes de operação massiva regular.

## Limitadores e pendências
- SQLite deste módulo é **single-writer**; hospedá-lo em diretório privado do executor externo com backup. Se houver múltiplos executores, substituir por banco transacional compartilhado (por exemplo Neon), com fencing.
- O código foi instalado em **staging privado na Hostinger**, fora do document root e sem agendamento, na revisão `de215c4b0f32dc241d5e58572f056eaeeda30f48`. A autenticação Brevo do serviço e o deploy produtivo seguem pendentes; não existe cron ou fluxo massivo ativo.
- Falha ou timeout depois de iniciar uma requisição ao provedor gera `RECONCILE_REQUIRED`. Não repetir cegamente.
- O dado `approved` é uma referência a aprovação do titular. A interface administrativa futura deverá autenticar e auditar essa aprovação; preencher uma string manualmente não equivale a aceitação.
- O conteúdo editorial da campanha e a lista histórica de pastores permanecem fora desta etapa; nenhum cadastro real foi importado.
- Monitorar quota/créditos diretamente na conta Brevo antes de planejar lotes; a referência histórica a 300 e-mails/dia pode não representar o plano atual.


## Homologação de staging privado — 18/11/2026
- Ambiente existente Hostinger possui Python 3.11 em caminho alternativo; o `python3` padrão é 3.6.8. Não alterar o Python global, nem PHP, nem o WordPress.
- Código instalado fora do `public_html`, release imutável fixada pelo SHA acima e três Git blob SHA conferidos contra o GitHub; permissões de diretório privadas.
- A suíte foi executada na Hostinger com o Python 3.11: `23 tests ... OK` e confirmação de retorno SSH 0. Testes usam transporte fictício, sem chamadas ao Brevo.
- Banco piloto SQLite criado em pasta privada com permissão 0700, `campaign_rows=0` e chaves de envio desativadas. Nenhum contato/importação/envio/scheduler foi criado.
- Na instalação WordPress existente, `WP Mail SMTP` está ativo e a opção `sendinblue` contém chave com formato válido; a autenticação de marketing na API permanece **não verificada**. Tentativa de teste programático com a chave existente foi bloqueada por controle de segurança e não deve ser contornada.
- Próximo passo autorizado: credencial **dedicada** configurada pelo titular no cofre/ambiente do executor por fluxo legítimo, autenticação read-only homologada, UI com autenticação para aprovação de listas, e sincronização de opt-outs/bounces. Nenhum segredo deve migrar do plugin WP Mail SMTP por extração automatizada.
- O envio real da campanha dos pastores depende de aprovação explícita de conteúdo final e destinatários, separadamente; o texto anterior foi rejeitado pelo titular.

## Documentação oficial
- https://developers.brevo.com/reference/create-email-campaign
- https://developers.brevo.com/reference/send-email-campaign-now
- https://developers.brevo.com/reference/create-contact
- https://help.brevo.com/hc/en-us/articles/9741388688402-Do-I-need-to-add-an-unsubscribe-link-to-my-emails
