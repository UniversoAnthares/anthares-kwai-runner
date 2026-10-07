# Lease — remoção de tokens de query string dos adaptadores sociais
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-07
RUN: none
JOB: MDE9nE00YIndrW2UFftCo3
COMMIT: pending
SUPERSEDES: 20261006-1325-lease-social-direct-adapters.md
EXPIRES: 2026-10-07T16:15:00Z

## Objetivo
Corrigir somente as verificações GET do Instagram/Threads para enviar o token no header `Authorization`, preservando o contrato de autenticação já usado por `req()` e sem executar chamadas externas.

## BASELINE_PROVEN
A auditoria estática encontrou `access_token` em query string nas URLs de verificação; `req()` já suporta o header `Authorization`.

## FAILED_AVOIDED
Não publicar em redes sociais, não alterar contas/credenciais, não habilitar a rota paga do X e não mexer no contrato de destination_key.

## SUCCESS_SIGNAL
As URLs de verificação não contêm token; o token é passado somente via header e os testes offline existentes continuam passando.

## FAILURE_SIGNAL
Token ainda aparece na URL/log, ou testes de autenticação/isolamento regredem.

## TEST_VALIDITY
Validação somente por inspeção do código e testes locais sem credenciais reais; nenhuma requisição de rede será realizada.
