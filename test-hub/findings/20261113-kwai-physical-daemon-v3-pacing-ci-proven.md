# Kwai: alinhamento do daemon Windows ao pacing Neon v3 — CI comprovado
STATUS: PROVEN
AREA: kwai
DATE: 2026-11-13
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43521536143
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43521536143/job/132216730660
COMMIT: 198648794359eeeff81a54447b02dd4347d3b542
SUPERSEDES: 20261113-kwai-physical-daemon-v3-pacing-running.md

## Resultado
Corrigido o contrato estático do daemon de kwai-public-post-proportional-v2 para kwai-public-post-proportional-06to23-v3, que é o valor publicado pelo Neon cortesqueue production 76. Validação de abertura 06h, fechamento 23h, cálculo proporcional e rejeição de window_open_at adulterado. Nenhum vídeo, credencial, Android, PC, banco ou fila foi utilizado para executar o teste.

## Evidência decisiva
Run #43521536143 completed/success; último step relevante:
CANONICAL_MODULES_AND_FAIL_CLOSED_GUARDS_PASS
KWAI_LOCAL_V3_WINDOW_06_23_AND_DUE_MATH_PASS
ALL_CANONICAL_WINDOWS_KWAI_REGRESSIONS_PASS

## Limites
Prova CI é somente de contrato/cálculo offline. Produção do daemon Windows permanece com versão antiga até integração e implantação coordenada. ACK locais obsoletos exigem conciliação read-only com Neon para liberar conta secundária; três locais confirmed e um cancelled. API legacy reconcile continua intencionalmente indisponível para evitar mutação sem prova. RLS production ainda sem políticas; cloud Android desabilitado. R$0, Oracle/CutMotions e publicação em GitHub Android fora de escopo.

SUCCESS_SIGNAL: offline CI success com sinais acima.
FAILURE_SIGNAL: qualquer prova de novo post, alteração do Neon ou regressão da janela 06-23.
TEST_VALIDITY: offline Python AST + Node tests, sem rede para Android/Kwai.
