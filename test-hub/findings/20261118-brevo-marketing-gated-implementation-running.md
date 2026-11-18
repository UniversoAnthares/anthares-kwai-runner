# Brevo Marketing API — primeiro contrato de implementação
STATUS: RUNNING
AREA: email
DATE: 2026-11-18
RUN: pending GitHub PR workflow
JOB: none
COMMIT: 2d70df9d096fa9eaa5bf391030e62d828a8b06b9
SUPERSEDES: none

## Objetivo
Implementar integração inicial de campanhas Brevo em branch isolada sem qualquer envio real ou importação de contatos da lista histórica.

## BASELINE_PROVEN
- `20261006-0946-email-campaign-preparation-proven.md`: core de preparação 9/9 testes.
- `20261006-0850-email-infrastructure-baseline-proven.md`: DNS de Brevo/Hostinger e caixa Hostinger.
- Teste Brevo via WordPress em 16/11/2026 foi recebido em Gmail; não equivale à integração deste novo módulo.

## FAILED_AVOIDED
Evitar SMTP transacional de marketing, envio por Gmail/Hostinger em massa, operação no PC, segredos em Git, reprocessamento após timeout e envios por mero fato de existir contato.

## SUCCESS_SIGNAL
CI offline do novo módulo executa testes de gate, consentimento, payload, list IDs, persistência, idempotência e regressão do core existente com logs de sucesso.

## FAILURE_SIGNAL
Erro de sintaxe, falha de contrato, gravação de dados sem gate, repetição em timeout, uso inadvertido de rede real ou disparo em ambiente de teste.

## TEST_VALIDITY
Código/testes com transporte fictício e switches OFF; aprova apenas a implementação em simulação. Autenticação real, envios e eventos de provedores exigirão fases separadas.

## Consequência
A branch não permite ativar mailing real. Aguardar CI e revisão, registrar resultado final append-only; não promover para produção antes de completar os gates.
