# Lease: bootstrap de sessão Grok, Manus e Perplexity
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## BASELINE_PROVEN
- Claude já está PROVEN em perfil Chrome separado, autenticado manualmente uma vez e reutilizado em desktop virtual oculto sem tocar no Chrome normal.
- Executor genérico oculto e probe genérico já foram versionados no repositório.

## FAILED_AVOIDED
- Não reutilizar o Chrome normal do usuário.
- Não usar headless puro para bootstrap de login quando o provedor bloquear Cloudflare/login interativo.
- Não usar automação por foco/SendKeys em janelas do usuário.

## Objetivo
Autenticar, um por vez, perfis Chrome dedicados para Grok, Manus e Perplexity, com autorização explícita do usuário para três janelas visíveis isoladas. Depois, fechar cada janela e validar reutilização oculta sem interação com o Chrome normal.

## SUCCESS_SIGNAL
Cada provedor fica autenticado em seu perfil dedicado; depois um probe oculto consegue carregar a interface autenticada e um teste simples retorna o marcador esperado sem processo residual.

## FAILURE_SIGNAL
Login não pode ser concluído, sessão não persiste no perfil dedicado, ou o provedor bloqueia o mecanismo mesmo após autenticação manual válida.

## TEST_VALIDITY
Falha de launcher, quoting, Python/Playwright ou executor remoto antes de a página do provedor carregar é HARNESS e não conta contra o provedor.

## Expiração
30 minutos a partir da criação deste finding.
