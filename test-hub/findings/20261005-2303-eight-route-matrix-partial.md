# Eight-route matrix green harness but login objective not proven
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381245242
JOB: 8-route matrix
COMMIT: 1af4812309808b4b58f7ae0a99c9723b0e8645dd
SUPERSEDES: none

## Objetivo
Explorar oito variantes de clique no pai ll_profile após estabilização.

## Resultado
Os 8 jobs terminaram success no harness, mas verde não equivale a login comprovado. O hub revelou um gate final Start now em testes correlatos; a geração seguinte já trata explicitamente esse gate. O inspector paralelo 37381259065 falhou e não deve ser usado como evidência positiva.

## Evidência decisiva
37381245242: 8/8 jobs success de execução. 37381259065: failure. Finding 20261005-2255 prova o gate "You're all set... Start now" com resource-id tiny_discovery_left_operation_btn. A matriz de 20 rotas 37381528807 já está em andamento e inclui esse tratamento.

## Consequência
Não repetir a matriz de 8. Promover a matriz pós-Start-now como fonte de decisão e exigir EDITABLES/AUTH_CANDIDATES ou mudança inequívoca de tela para considerar rota funcional.
