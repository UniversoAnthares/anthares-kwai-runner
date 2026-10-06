# Lease: endurecer executor Claude oculto
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Generalizar o fluxo Claude oculto já comprovado em um executor reutilizável, validar com múltiplos prompts reais e fechar o lease com evidência.

## BASELINE_PROVEN
`test-hub/findings/2026-10-05-claude-hidden-profile-post-success.md` — perfil dedicado autenticado + desktop virtual oculto + CDP/Playwright enviaram `TESTE_OK_CLAUDE` com sucesso.

## FAILED_AVOIDED
- Headless puro foi bloqueado pelo Cloudflare; este teste mantém Chrome headful em desktop virtual oculto.
- Não reutilizar nem copiar cookies do Chrome normal.
- Não usar foco/SendKeys nem automação de abas visíveis.

## SUCCESS_SIGNAL
Runner aceita prompt arbitrário, retorna JSON estruturado com resposta não vazia, fecha o Chrome isolado e passa em pelo menos três prompts independentes.

## FAILURE_SIGNAL
Login perdido, Cloudflare bloqueando novamente, ausência de caixa de prompt, ausência de resposta, timeout ou processo residual do perfil dedicado.

## TEST_VALIDITY
Falha de quoting, import, launcher, CDP ou seletor do harness é INVALID e não conta contra a hipótese Claude.

## Expiração
2026-10-05 21:15 -04:00
