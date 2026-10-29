# Instagram Graph preflight: aceite limitado ao deslocamento de executor
STATUS: PROVEN
AREA: instagram-graph-preflight/cloud-offload
DATE: 2026-10-29
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40913732546
JOB: 123588319591
COMMIT: 3d7273170d3b17c6acdb164c27b4cbe306888ea7
SUPERSEDES: 20261029-instagram-cloud-preflight-existing-auth-error-partial.md

## Evidência de execução externa
O GitHub atribuiu o runner GitHub Actions 1000049354, com sistema ubuntu-24.04. Checkout e instalação do Python foram concluídos; o passo de leitura HTTPS da API Instagram foi executado. O job saiu código 4, INSTAGRAM_TOKEN_CONFIG_PRESENT=True, INSTAGRAM_GRAPH_PROFILE_CHECK=4. O mesmo teste no runner Windows em 22/10, run 39772578756, job 119803510175, terminou com os mesmos marcadores e código do programa 4. Não houve publicação nem mutação.

## Escopo de aceitação
PROVEN exclusivamente que a checagem agora pode ser executada integralmente na nuvem sem dependência Windows. A identidade Graph continua AUTH_ERROR pré-existente e a funcionalidade de validação da conta permanece PARTIAL; o erro não foi resolvido nem encoberto no resultado CI. A PR #1909 substitui a origem de execução do mesmo GET read-only e conserva o erro como falha explícita. Manter o incidente de autenticação como pendência independente, sem requisição de novos segredos e sem novas tentativas equivalentes. O PC permanece necessário para outras rotas.

## Conciliação e concorrência
Comparados workflow GitHub main e GitLab main: ambos Windows, equivalentes no campo do runner. Alteração de somente uma workflow na PR; os outros jobs e perfis ficam intocados. Revisão do baseline local precede este aceite de offload.
