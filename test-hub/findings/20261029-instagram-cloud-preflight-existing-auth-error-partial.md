# Instagram Graph remote preflight — same authentication failure on Windows and cloud
STATUS: PARTIAL
AREA: instagram-graph-preflight/cloud-offload
DATE: 2026-10-29
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40913732546
JOB: 123588319591
COMMIT: 3d7273170d3b17c6acdb164c27b4cbe306888ea7
SUPERSEDES: lease-20261029-instagram-graph-hosted-preflight.md

## Evidência
GitHub-hosted runner GitHub Actions 1000049354, ubuntu-24.04, executou todos os passos até a consulta Graph. Log: INSTAGRAM_TOKEN_CONFIG_PRESENT=True; INSTAGRAM_GRAPH_PROFILE_CHECK=4; exit_code=4. A exceção é InstagramAPIError da API; esse diagnóstico não determina se token expirou, perdeu escopo ou se host/versão de API diverge.
Baseline Windows self-hosted run 39772578756, job 119803510175, em 22/10/2026: os mesmos marcadores INSTAGRAM_TOKEN_CONFIG_PRESENT=True e INSTAGRAM_GRAPH_PROFILE_CHECK=4. Assim, o problema de autenticação precede a migração e não foi causado pelo runner Ubuntu.

## Consequência
PR #1909 permanece isolada, sem promoção ao main. Capacidade de execução off-PC comprovada; aceitação completa da verificação oficial de identidade PENDENTE da correção/validação da credencial/endpoint. Evitar novos disparos equivalentes sem alteração causal. Não houve publicação, alteração de token nem gravação de sessão.
