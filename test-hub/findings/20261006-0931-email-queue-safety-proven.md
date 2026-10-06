# Email queue safety core
STATUS: PROVEN
AREA: email
DATE: 2026-10-06
RUN: local authorized machine
JOB: AI Commander python unittest
COMMIT: b19511c3ca580b931785b55fd198e4d6522fe09d
SUPERSEDES: test-hub/findings/20261006-0926-lease-email-queue-implementation.md

## Objetivo
Converter a arquitetura de campanha em código testável sem realizar qualquer envio.

## Resultado
PROVEN: 6/6 testes passaram em clone fresco. O core normaliza/deduplica email, preserva múltiplas proveniências, exige aprovação explícita da campanha e do conjunto de destinatários, revalida suppression no lease, isola provider, limita batch diário e propaga hard bounce para suppression global. O workflow email-queue-safety.yml também foi adicionado para regressão automatizada. Nenhum provider de rede existe no módulo e nenhum email foi enviado.

## Evidência decisiva
python -m unittest discover -s tests -p test_email_queue.py -v => Ran 6 tests; OK.
Commits: a23e044f email_queue.py; c6b9005b tests; b19511c3 workflow.

## Consequência
Preservar o core como camada provider-neutral. Próximo agente pode implementar adapters Brevo/Resend atrás desta interface, mantendo envio desabilitado por padrão e usando fake/sandbox até campanha+recipient_set aprovados. A futura campanha de pastores continua sem autorização de disparo.
