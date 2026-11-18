# Brevo Marketing — verificação de prontidão somente leitura
STATUS: PROVEN
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44351992986
JOB: 134969830129
COMMIT: 826816e0306bf7c0412ebbb8e225c384e072c729
SUPERSEDES: 20261118-brevo-marketing-gated-offline-proven.md

## Objetivo
Acrescentar consulta autenticada de conta, campanhas e listas na API Brevo sem qualquer ação de envio; validar que relatórios de prontidão não incluem credenciais.

## Resultado
PROVEN em CI com transporte falso: 18/18 testes Brevo e 9/9 testes de regressão do sistema original passaram. Sintaxe Python aprovada. Branch isolada na PR draft #2656; produção sem alteração.

## Evidência decisiva
Log: `Ran 18 tests ... OK`; em seguida `Ran 9 tests ... OK`. O workflow define `BREVO_API_KEY=''` e `BREVO_LIVE_SEND_ENABLED=0`. As verificações adicionais exercitam apenas GET, validam paginação/filtros e retornam estados sem credenciais.

## Limitação
Esta execução não confirma existência da credencial no executor externo nem funcionamento de API Brevo real. É preciso conectar secret ao runtime autorizado e fazer probe GET real, sem envio e sem importação de mailing, para completar a integração operacional. Antes de enviar qualquer campanha, manter aprovação dupla de conteúdo e lista; a campanha anterior foi rejeitada pelo titular e não pode ser reaproveitada.
