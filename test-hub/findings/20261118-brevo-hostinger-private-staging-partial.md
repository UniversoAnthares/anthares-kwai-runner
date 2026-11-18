# Brevo Marketing — staging privado Hostinger, implementação segura
STATUS: PARTIAL
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44357868937
JOB: 134990768414
COMMIT: de215c4b0f32dc241d5e58572f056eaeeda30f48
SUPERSEDES: 20261118-brevo-audience-fingerprint-proven.md

## Objetivo
Instalar e verificar o módulo de mailing Brevo em executor externo Hostinger, mantendo campanhas e importações reais desligadas.

## Resultado comprovado
- **PROVEN (código e QA offline)**: GitHub Actions 23/23 testes Brevo e 9/9 regressões do core. Em Hostinger, Python 3.11.18 executou a mesma suíte: `Ran 23 tests in 0.090s; OK; HOST_BREVO_TEST_PASS`, retorno SSH 0.
- **PROVEN (integridade e armazenamento)**: instalação isolada privada, fora do document root, com três Git blob SHA idênticos aos arquivos do commit informado. Release e link atual verificados por consulta SSH após resposta inicialmente ambígua do controlador. Banco SQLite criado vazio (`campaign_rows=0`), diretório com permissão 0700.
- **PROVEN (configuração WP existente)**: WP Mail SMTP 4.10.4 ativo, remetente `sendinblue` e chave API presente com formato Brevo. O valor do segredo não foi impresso, armazenado, copiado nem incluído no código.
- **PENDENTE**: autenticação independente do novo módulo com a API Brevo, proveniência/autorização e importação da lista, webhook de unsubscribe/bounce, interface de controle, scheduler e envio de teste real. Requisição que tentava utilizar a chave do plugin foi bloqueada pelo controle de segurança. Não repetir por rota alternativa.

## Evidência decisiva
- SHA em Hostinger: `brevo_marketing.py` = `5c3b04d37a661eb2e189b95862c5c00faeb61c6d`; `brevo_campaign_ledger.py` = `65b875121d3ca06aeb4d84618a55512dd08fcfbf`; `tests/test_brevo_marketing.py` = `108b823cd5fea697da7e3e1e0fa1b7dfcb7bc8ee`.
- Hostinger Python 3.11.18 acessível por caminho alternativo, Python padrão 3.6.8; instalação sem mudança no PHP/WordPress.
- `BREVO_LIVE_SEND_ENABLED=0` no executor testado, sem API key, env de sincronização/rascunho/testes desativadas.
- `CampaignLedger` iniciou estrutura SQLite sem contatos e nenhuma campanha.

## Consequência
Permitir continuidade técnica por integração de **credencial dedicada** em cofre autorizado, sem extração do segredo do WP Mail SMTP e sem contornar controles de segurança. Requerer prova read-only com API real antes de conectar UI/scheduler. Manter PR #2656 em revisão, sem merge para o main nem ativação de campanha; rejeição editorial anterior continua válida. Não confundir staging privado e teste mock com entrega real.
