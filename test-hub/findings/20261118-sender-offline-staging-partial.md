# Sender marketing — contrato offline e staging Hostinger
STATUS: PARTIAL
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44394247824
JOB: 135119769000
COMMIT: 52f5889efc95fa94ee5575bb8f4ce75d42ec97a0
SUPERSEDES: 20261118-brevo-405-after-key-review-blocked.md

## Objetivo
Preparar Sender API v2 como provedor alternativo de campanhas; preservar a estrutura existente Brevo, o WordPress, a caixa de email Hostinger e os gates de aprovação e supressões.

## BASELINE_PROVEN
Brevo permanece autenticado por GET na Hostinger. Envios reais de marketing parados devido a POST /emailCampaigns HTTP 405 e webhooks marketing GET HTTP 403. PR Brevo #2656 em revisão.

## Implementação
- Branch independente `feat/sender-marketing-gated-20261118`, PR draft #2657 sobre a branch de trabalho Brevo para facilitar review e preservar código existente.
- `sender_marketing.py`: endpoints Sender v2, rascunhos, leitura de campanha/grupo, hash de audiência e proteção contra alterações, unsubscribe HTML obrigatório e dispatch desligado por default.
- `sender_campaign_ledger.py`: SQLite local com registro imutável, dupla aprovação exigida, estados de reconciliação e bloqueio de tentativa repetida quando a confirmação do provedor é incerta.
- `sender_readonly_check.py`: diagnóstico read-only sem exibir token ou destinatários.
- Testes CI: **27/27 Sender** + **9/9 regressões Anthares**, sintaxe Python aprovada. Testes remotos Hostinger: **27/27 Sender**, sem token/sem rede Sender real.

## Instalação comprovada
- Release corrente na Hostinger: `releases/52f5889efc95fa94ee5575bb8f4ce75d42ec97a0`, pasta privada fora do `public_html`.
- `sender_readonly_check.py` Git blob SHA confirmado `21285563345ace089aa648ec22dedd15cedbf2a7`.
- SQLite `sender_campaigns.sqlite3`: criado em pasta 0700, modo arquivo 0600 e **0 campanhas**.
- Arquivo destinado ao token criado em `/home/u566597497/domains/anthares.us/anthares-sender-mailer/sender-api-token.txt`, modo 0600 e **0 bytes**, linked ao runtime privado. Nenhum token real armazenado até o momento.
- Nenhum cadastro Sender detectado nas abas do navegador, caixa Hostinger ou busca da conta Gmail conectada. Isso não comprova ausência de eventual cadastro externo.
- Nenhuma alteração do DNS, WordPress, configurações da Brevo ou outras automações; nenhum contato importado; nenhuma mensagem enviada.

## Próximas condições
É necessária conta Sender e token próprio criado pelo titular em `Account settings → API access tokens`; o usuário deverá manter a credencial fora do chat. Após gravá-la no arquivo privado Hostinger, validar GET /groups e GET /campaigns pelo diagnóstico já instalado. Em seguida homologar domínio/remetente no Sender, grupo controlado, rascunho e envio de teste permitido, descadastros e painel de autorizações autenticadas. Nenhum mailing de pastores aprovado nesta etapa. Não ativar os switches de envio em lote até esses requisitos terem prova real.

## Limitações de prova
Os testes de CI são de contrato simulado e não implicam login real, rascunho remoto, roteamento SMTP/DKIM ou entrega. O SMTP da Hostinger permanece separado do marketing e a API transacional não substitui a API de campanhas.
