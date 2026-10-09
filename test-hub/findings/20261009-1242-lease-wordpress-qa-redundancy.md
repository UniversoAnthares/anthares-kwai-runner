# Lease — WordPress QA multi-IA, runner failover e espelhos redundantes
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-09
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Ampliar a autocorreção do QA do anthares-wordpress para Gemini, Groq, Cloudflare, Mistral, NVIDIA, Hugging Face, Vercel e GitHub Copilot; corrigir a indisponibilidade do GitHub Actions evidenciada pelo run 37891612002; reconciliar GitHub/GitLab sem perda e implantar redundância com verificação de divergência.

## Baseline
BASELINE_PROVEN: GitLab main b0c6cf63f8a75ca71c4d8c5c1e25dc35fc64f4be com pipeline 2928884357 PASS; GitHub main bbe1eed2ea1f19bb32954420317ef602d66480ff; ambos descendem de 85aa1ed09076ba18bc880f397fe3e8a01afe9e09 e o ajuste PDF do GitHub já existe no conteúdo do GitLab.
FAILED_AVOIDED: run GitHub 37891612002 terminou failure antes de executar qualquer step; a nova arquitetura não pode depender de um único scheduler/runner GitHub.
SUCCESS_SIGNAL: provedores adicionais participam do roteamento de autocorreção; Copilot recebe fallback por issue/agente quando disponível; CI alternativo executa QA; espelhos convergem por conteúdo/histórico reconciliado; detector de drift falha fechado e produz evidência.
FAILURE_SIGNAL: perda de commit/conteúdo em qualquer espelho, QA de código regressivo, autocorreção sem gates ou sincronização cega/force.
TEST_VALIDITY: validar heads imediatamente antes/depois das mutações e exigir pipeline/linters reais; falha de infraestrutura sem steps não conta como falha de código.

## Lease
Holder: ChatGPT
Expires: 2026-10-09T13:10:00Z
Scope: anthares-wordpress QA/autofix/mirror redundancy only.
