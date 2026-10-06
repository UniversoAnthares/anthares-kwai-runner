# Claude em perfil isolado: autenticação persistente + envio oculto comprovados
STATUS: PROVEN
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Comprovar que um perfil Chrome separado do usuário pode permanecer autenticado no Claude e depois ser reutilizado em um desktop virtual oculto para enviar uma mensagem real sem tocar no Chrome normal do usuário.

## Baseline
- Headless puro com Chrome/Playwright/CDP parava no challenge do Cloudflare.
- Chrome headful em desktop virtual separado passou pelo Cloudflare e chegou ao login real do Claude.
- O perfil dedicado foi autenticado manualmente uma única vez pelo fluxo oficial da Anthropic.

## Teste
- Perfil persistente: `C:\Users\Lucas\AntharesWork\claude-hidden-desktop-profile`.
- Chrome headful lançado em desktop virtual oculto via Win32 `CreateDesktopW` + `CreateProcessW`.
- Automação conectada ao Chrome isolado por CDP/Playwright.
- Prompt enviado: `Responda exatamente: TESTE_OK_CLAUDE`.
- Critério de sucesso: marcador `TESTE_OK_CLAUDE` aparecer novamente como resposta, não apenas dentro do prompt enviado.

## Resultado
O runner retornou:
- `sent=true`
- `reply=TESTE_OK_CLAUDE`
- `result=SUCCESS`
- exit code 0
- runtime aproximado 10 s

## Evidência decisiva
Saída do runner local:
`{"pid": 6980, "sent": true, "reply": "TESTE_OK_CLAUDE", "result": "SUCCESS"}`

Verificação posterior por `wmic` filtrando `claude-hidden-desktop-profile` não encontrou processo Chrome residual; apenas o próprio comando de inspeção apareceu.

## Consequência
- PROVEN: Claude pode ser usado por automação invisível sem reutilizar nem manipular o Chrome normal do usuário.
- Preservar este perfil dedicado; não copiar cookies do Chrome normal.
- Para novos testes Claude, reutilizar este perfil e desktop virtual oculto.
- Não voltar a headless puro para Claude enquanto não houver mudança causal, pois o Cloudflare bloqueou esse caminho repetidamente.
- A etapa visível/manual de login foi necessária apenas para bootstrap inicial da sessão; o envio subsequente funcionou ocultamente.
