# Anthares Mailing — Resend Broadcasts (homologação 18/11/2026)

**Estado:** código e testes aprovados; staging privado Hostinger instalado; criação de conta, autenticação real e verificação do domínio pendentes.

## Escopo
O Resend é a alternativa avaliada após o Sender. Utilizar **Marketing Broadcasts** (API `/broadcasts`) e segmentos/contatos da API Resend. A rota transacional `/emails` fica fora do mailing para pastores.

## Evidências
- GitHub: [PR draft #2658](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2658), branch `feat/resend-broadcasts-gated-20261118`.
- CI: [execução 44448379389](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44448379389): 18 contratos Resend e 9 testes de regressão passaram.
- Hostinger: release `736570e897f7650fd46fb3ec2aa8d34256475c2e`, diretório `/home/u566597497/.anthares-resend-mailer/current`, fora de `public_html`.
- Integridade: blob de `resend_marketing.py` no Hostinger = `07ddfe13fc8546e4f3b5d89c20636357b20c5259`.
- Testes offline na Hostinger: 18 testes Resend aprovados, ambiente Python 3.11.
- Arquivo de futura API key: `domains/anthares.us/anthares-resend-mailer/resend-api-key.txt`, vazio, modo 0600 e pasta restrita; linked ao staging privado.
- Sem registro de nova conta em `contato@anthares.us` até a pesquisa inicial; nenhum cadastro Resend confirmado.

## Funcionalidade preparada
- `resend_marketing.py` implementa consultas GET de `/segments`, `/broadcasts`, `/broadcasts/:id` e `/contacts?segment_id=...` com paginação cursorizada, validação do estado descadastrado e comparação com supressões globais.
- `ResendBroadcastDraft` exige `{{{RESEND_UNSUBSCRIBE_URL}}}`, segmento UUID, remetente fixo e conteúdo HTML válido.
- `create_draft` mantém `RESEND_DRAFT_WRITE_ENABLED=0` por padrão e jamais inclui `send=true`.
- `send_broadcast` sempre recusa envio: integração de aprovação auditável ainda pendente.
- `resend_readonly_check.py` consulta somente GET, usa chave em arquivo privado, verifica permissões e não revela credenciais.

## Cadastro: impedimento concreto
O formulário oficial `https://resend.com/signup` abriu corretamente no navegador remoto e no Chrome headless isolado. Exige e-mail e senha de no mínimo 12 caracteres, combinando letras, números e símbolos. A preparação de uma senha forte privada no Hostinger foi concluída com arquivo modo 0600, mas a tentativa subsequente de construir uma rotina automatizada de preenchimento por conexão remota **foi barrada pelas configurações de segurança da execução**. A operação de cadastro foi interrompida, sem contornar essa restrição. Não existe cofre 1Password integrado ao Browserless para preenchimento seguro. Nenhum POST de cadastro, confirmação por e-mail ou login foi comprovado. Nenhuma senha ou chave foi incluída no GitHub, no chat ou no log.

## Requisitos para operação real
1. Criar a conta gratuita Resend para `contato@anthares.us` por fluxo de autenticação autorizado.
2. Confirmar e-mail e domínio `anthares.us`; verificar DKIM/SPF sem interromper MX da Hostinger, Brevo ou outros serviços.
3. Gerar API key restrita e armazenar no arquivo privado preparado; testar GET de segmentos e campanhas.
4. Criar segmento de teste só com caixa controlada pelo titular, validar descadastros e testar um rascunho aprovado.
5. Implementar proteção de tentativas únicas/ledger e aprovação autenticada da mensagem e destinatários antes de habilitar envio real; homologar recebimento e eventos de bounce/unsubscribe.
6. A lista histórica de pastores só pode ser importada após análise de procedência, base e autorização dos contatos. O plano gratuito do Resend é limitado a 1.000 contatos de marketing; necessidade de plano superior depende do tamanho real da audiência.

## Fontes oficiais
- https://resend.com/docs/api-reference/broadcasts/create-broadcast
- https://resend.com/docs/api-reference/contacts/list-contacts
- https://resend.com/docs/api-reference/pagination
- https://resend.com/pricing?product=marketing
