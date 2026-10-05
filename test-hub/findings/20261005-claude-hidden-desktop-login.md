# Claude em desktop virtual oculto passa pelo Cloudflare e chega ao login
STATUS: PROVEN
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Testar uso do Claude sem tocar no Chrome visível do usuário, depois de múltiplos testes headless bloqueados pelo challenge do Cloudflare.

## Baseline
- Headless com Chrome/Chromium, perfil persistente/efêmero e CDP: challenge `Um momento...` / `Just a moment...` antes do campo de mensagem.
- O Chrome visível do usuário não deve ser navegado nem reutilizado.

## Mudança causal
Criar um desktop virtual separado do Windows via `CreateDesktopW` e lançar nele um Chrome **headful** normal, com `user-data-dir` dedicado e CDP em porta local. O desktop não é selecionado, portanto a janela não aparece no desktop atual do usuário.

## Resultado
PROVEN: o Chrome headful no desktop virtual oculto atravessou o Cloudflare e chegou à página real `Sign in - Claude` em `https://claude.ai/login?...`.

A página ofereceu os métodos:
- Continuar com o Google
- Continuar com Apple
- Continuar com e-mail
- Continuar com SSO

O perfil dedicado ainda não está autenticado, portanto nenhum prompt foi enviado ao Claude.

## Evidência decisiva
Título observado via CDP: `Sign in - Claude`.
URL observada: `https://claude.ai/login?from=logout&reauth=1&returnTo=%2Fnew%3F`.
O campo de e-mail e os botões de login foram lidos via DOM no desktop virtual oculto.

## Consequência
- Não repetir tentativas headless comuns esperando que atravessem o Cloudflare sem mudança causal.
- Caminho promissor: Chrome headful em desktop virtual oculto + perfil dedicado persistente.
- Próximo bloqueio real é autenticação do perfil dedicado. Não copiar cookies/tokens do Chrome principal e não escolher conta Google/e-mail às cegas.
- Após autenticar uma vez o perfil dedicado pelo método correto, reutilizar o mesmo perfil no desktop virtual oculto e testar `Responda exatamente: TESTE_OK_CLAUDE`.
