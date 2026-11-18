# Brevo Marketing — destinatários imutáveis depois da aprovação
STATUS: PROVEN
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44355584379
JOB: 134982689450
COMMIT: e9b489984ab43240ee8559481b11d3c51713109c
SUPERSEDES: 20261118-brevo-readonly-readiness-offline-proven.md

## Objetivo
Impedir que uma campanha enviada após uma aprovação alcance destinatários alterados dentro do mesmo listId Brevo.

## Resultado
**PROVEN somente em testes locais simulados na CI**: 20/20 contratos Brevo e 9/9 testes do core anterior, sintaxe Python aprovada. A aprovação da lista agora registra hash SHA-256 da composição de e-mails elegíveis, conferido novamente antes de enviar. Foi corrigida a leitura do campo oficial `listId` retornado por GET /emailCampaigns/{campaignId}. Contatos bloqueados em Brevo são excluídos da composição aprovada.

## Evidência decisiva
Log do job: `Ran 20 tests ... OK`; regressão `Ran 9 tests ... OK`. Testes novos comprovam falha fechada quando membros da lista mudam mesmo com listId igual e exigência de fingerprint. Zero credenciais no workflow, zero chamadas API reais.

## Limitações
- Integração ainda em PR draft #2656, não implantada no WordPress nem em host externo.
- Chave Brevo no executor externo não confirmada. WordPress/WP Mail SMTP teve envio transacional comprovado em 16/11, sem prova de acesso do novo módulo de marketing.
- Credenciais Brevo ausentes apenas no ambiente de variáveis Windows consultado em 18/11; isso não demonstra ausência do segredo no WordPress.
- Antes de envio real: aprovação de mensagem e destinatários pela interface autenticada, snapshot de audiência válido e teste real isolado no executor com segredo autorizado. O conteúdo da campanha anterior foi rejeitado e segue fora de uso.
