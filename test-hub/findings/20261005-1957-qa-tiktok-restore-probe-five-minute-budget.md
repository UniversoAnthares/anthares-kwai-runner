# TikTok restore probe exceeded operational 5-minute evidence budget
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388273031
JOB: 112026953805
COMMIT: c7a84b8a44e440beedec9fe8baee7e887e6b34fc
SUPERSEDES: none

## Objetivo
Aplicar o critério operacional do projeto: teste que passa de ~5 minutos sem produzir o sinal causal útil esperado deve ser tratado como mecanismo inadequado, não deixado consumindo tempo.

## Resultado
O run iniciou 23:24:08Z e continuava in_progress após 23:29:28Z. Nesse intervalo a API Render já confirmou a revisão fc26d51a live às 23:25:09Z, mas o workflow permaneceu preso no gate de revision/espera antes do resultado de restore. O job publish permaneceu skipped.

## Evidência decisiva
GitHub run 37388273031 ainda in_progress mais de cinco minutos após created_at. Render deploy exato já estava live. Finding 20261005-1955 explica que /health usa WORKER_RUNTIME_REV de ambiente e pode não acompanhar o commit implantado.

## Consequência
Não esperar este mecanismo como prova útil nem repetir a mesma espera de 40x10s. Se terminar por timeout/revision-not-ready, classificar harness invalid. CHAT 3 deve substituir o gate por verificação de deploy que reflita a revisão real e manter o publish desligado até sessão/identidade serem provadas.