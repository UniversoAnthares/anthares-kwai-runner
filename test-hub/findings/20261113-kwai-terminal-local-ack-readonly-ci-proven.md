# Kwai: consulta terminal autenticada para reconhecer ACKs locais — CI aprovado
STATUS: PROVEN
AREA: kwai
DATE: 2026-11-13
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43522789422
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43522789422/job/132220965782
COMMIT: f7246d6daa685cb530e8bdfc478cac33999f67e5
SUPERSEDES: 20261113-kwai-terminal-local-ack-readonly-running.md

## Resultado
Implementada somente em branch de código uma leitura autenticada kwai-job-terminal-read, exigindo assinatura RSA do executor físico e cruzando id exato, conta, lease_generation, estado, prova server-side e callback WordPress completed. A resposta é somente estado terminal; não concede lease e não executa UPDATE/INSERT/DELETE. Cliente físico consulta terminal; daemon reconhece confirmed e cancelled somente quando correspondentes ao recibo local e à conta, e registra em ACK existente sem republicar nem reenviar callback.

## Evidência decisiva
GitHub Actions #43522789422 completed/success.
Node: pass 37, fail 0. Python AST: KWAI_TERMINAL_ACK_FAIL_CLOSED_READONLY_PASS e ALL_CANONICAL_WINDOWS_KWAI_REGRESSIONS_PASS.
Teste isolado rejeitou papel diferente de físico, geração divergente, conta cruzada, URL de autor diferente, ausência de confirmação WordPress, prova ausente, estado uncertain e id inválido.

## Limites
Código ainda requer merge, QA, implantação controlada na função Neon e substituição coordenada do processo Windows existente para efeito operacional. Não houve publicação nova, mutação do Neon ou modificação de ACK real. RLS production ainda desabilitado; corte cloud permanece bloqueado.

SUCCESS_SIGNAL: CI pass 37 fail 0, Python ACK pass; filas intactas.
FAILURE_SIGNAL: qualquer alteração na fila, autorização alargada ou nova postagem.
TEST_VALIDITY: executado inteiramente no runner de testes, com mocks de SQL/JavaScript e AST Python.
