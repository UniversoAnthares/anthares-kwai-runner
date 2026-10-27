# Android CI routing-contract schema — hosted proof
STATUS: PROVEN
AREA: github / ci-android-routing
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40499940218
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40499940218/job/122174804640
COMMIT: 49cfd007c572488dad90b8908ce32baa0d3f5dae
SUPERSEDES: test-hub/findings/lease-20261027-android-routing-schema-chatgpt.md

## Causa e correção
A falha anterior no run 40494510557 / job 122156438512 foi KeyError em browser_execution.priority. O workflow usava três caminhos obsoletos. Atualizados para browser_execution.backend_priority, retired.circleci e providers.gitlab_ci. Nenhuma regra de roteamento, despachante, dispositivo, sessão ou publicação foi alterada.

## Evidência decisiva
Run 40499940218 / routing-contract job 122174804640: Ran 20 tests in 0.002s, OK e CIRCLECI_RETIRED_ROUTING=PASS. Contrato provado em GitHub Actions real. O job de emulador Android no mesmo workflow é uma avaliação separada, sem publicação, e seu resultado não muda a conclusão do teste de roteamento.

## Consequência
A correção do teste é aprovada para merge normal após os gates do repositório. O sinal de aceitação restringe-se ao routing-contract. Não alegar login Kwai, publicação, cancelamento real por cota, ou autenticação WordPress a partir deste resultado.
