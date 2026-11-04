# Telegram relay — idempotência e resposta de erro
STATUS: RUNNING
AREA: telegram-relay
DATE: 2026-11-03
RUN: none
JOB: ChatGPT, branch fix/relay-send-idempotency-20261103
COMMIT: none
SUPERSEDES: none

## BASELINE_PROVEN
Relay main 8eefc5d373ad02e53a5684c78c61291d1f63a9f7. SQLite envia reserva antes de MTProto e retorna duplicate=true ao repetir, inclusive após falha; FastAPI HTTPException envelopa mensagem em detail, enquanto WordPress procura message no topo. Sem endpoint ativo na Railway.

## FAILED_AVOIDED
Nenhum envio real, login, novo serviço ou custo. Somente código e testes offline. Proteger sesssões existentes, estado incerto e respostas de erro.

## SUCCESS_SIGNAL
Apenas confirmações de Telegram geram duplicate=true; falha incerta bloqueia retries; erro de relay é legível para WordPress. Migração de banco preserva registros antigos como incertos.

## FAILURE_SIGNAL
Reenvio duplicado, falsa confirmação, regressão criptográfica ou schema incompatível.

## TEST_VALIDITY
Testes unitários offline verificam SQLite e HMAC; aceitação real requer relay hospedado, secrets existentes e conta de teste autorizada.

## Lease
Área telegram-relay exclusiva por 30 minutos, sem sobreposição com publicadores ou arquivos de WordPress. Encerrar com finding append-only.
