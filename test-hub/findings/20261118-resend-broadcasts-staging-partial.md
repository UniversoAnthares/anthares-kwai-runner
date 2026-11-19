# Resend Broadcasts: contrato offline e staging privado
STATUS: PARTIAL
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44448379389
JOB: 135305988890
COMMIT: 736570e897f7650fd46fb3ec2aa8d34256475c2e
SUPERSEDES: none

## Objetivo
Preparar o Resend para o mailing Anthares após o bloqueio de cadastro Sender; preservar Brevo, WordPress, MX Hostinger e não enviar campanhas.

## Resultado
- **PROVEN (CI simulado):** 18 testes específicos Resend e 9 testes regressivos aprovados na execução 44448379389.
- **PROVEN (staging servidor):** arquivos privados instalados em Hostinger sob release acima, hash blob do adaptador `07ddfe13fc8546e4f3b5d89c20636357b20c5259`; 18/18 testes Resend passaram em Python 3.11 do Hostinger. Shell de instalação registrou sucesso e erro residual de CR final, reconciliado por leitura independente da release e blob corretos.
- **PROVEN (segurança):** arquivo de API key futuro modo 0600, 0 bytes, fora da pasta pública, sem token e sem envio. Método `send_broadcast` intencionalmente bloqueado.
- **PROVEN (site real):** página `https://resend.com/signup` acessível em navegador remoto e Chrome headless, com exigência de senha. Houve bloqueio por política de segurança na tentativa de automação de preenchimento da senha; não foi contornado. Sem prova de conta criada.
- Nenhum registro de domínio, alteração de DNS, plano pago, importação de contato ou campanha foi realizada.

## Limites
Sem chave API Resend não houve teste de GET autenticado, rascunho remoto, entrega ou relatórios. Sem aprovações separadas e prova de consentimento não habilitar mailing massivo. A PR #2658 permanece draft.

## Próximo passo
Criar conta gratuitamente por fluxo de credencial seguro autorizado, validar remetente e domínio, gerar chave privada, homologar GET e rascunho técnico; somente então abordar aprovação de campanha e destinatários.
