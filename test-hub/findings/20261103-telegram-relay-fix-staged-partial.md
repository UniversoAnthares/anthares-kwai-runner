# Conector Telegram — idempotência staged
STATUS: PARTIAL
AREA: telegram-relay
DATE: 2026-11-03
RUN: none
JOB: https://github.com/UniversoAnthares/anthares-telegram-relay/pull/5
COMMIT: 39432448ce52490b55d93648bd320c05f5306a9c
SUPERSEDES: test-hub/findings/20261103-telegram-relay-idempotency-lease.md

## Resultado
Branch com esquema de send status e migração fail-closed (legado uncertain), reserva nova distinta de pending, transição confirmed após retorno positivo do MTProto, estado uncertain após exceção. Respostas de HTTPException agora mantêm message/code no topo para o cliente WordPress. Testes offline atualizados no código e ainda não executados.

## Evidência
PR #5 com app/core.py, app/main.py e tests/test_core.py. Sem deploy nem sessão Telegram usada. Sem prova de saúde na Railway. Nenhum pagamento, infraestrutura ou consumo novo.

## Consequência
Executar unit tests e checagens de infraestrutura/volume antes do merge; implantar somente em relay com variáveis de ambiente e volume já autorizados. Confirmar endpoint de saúde, callback, OTP com conta de teste, postagem real autorizada e revogação antes de abrir o recurso a usuários. Lease encerrado; nova mutação exige preflight.
