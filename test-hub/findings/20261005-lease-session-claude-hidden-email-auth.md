# Lease: autenticação Claude em desktop virtual oculto por e-mail
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: `20261005-claude-hidden-desktop-login.md` — Chrome headful em desktop virtual oculto passa pelo Cloudflare e chega ao login real do Claude.
FAILED_AVOIDED: não usar headless comum; não tocar no Chrome visível; não copiar cookies/tokens; não escolher conta Google às cegas.
SUCCESS_SIGNAL: perfil dedicado do desktop oculto autenticado legitimamente no Claude e envio de `Responda exatamente: TESTE_OK_CLAUDE` com confirmação da resposta.
FAILURE_SIGNAL: fluxo de e-mail exige senha/segundo fator não disponível, endereço não corresponde a conta Claude existente, ou não chega código/link utilizável ao Gmail conectado.
TEST_VALIDITY: harness deve permanecer no desktop virtual oculto, processo/PID exclusivo, sem navegação no Chrome principal; erros do harness são INVALID TEST, não falha da hipótese.
EXPIRA: 2026-10-05T19:59:00-04:00

## Objetivo
Tentar autenticar o perfil Claude isolado usando o fluxo oficial `Continuar com e-mail`, com `lucasyahn@gmail.com`, e ler eventual código/link de autenticação pelo conector Gmail autorizado pelo usuário.
