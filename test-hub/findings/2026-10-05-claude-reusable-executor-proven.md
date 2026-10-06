# Claude reutilizável oculto: runner generalizado e self-test triplo
STATUS: PROVEN
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: e84323dd17719c76f69d98cd8f5969cf8878595e
SUPERSEDES: none

## Objetivo
Fechar o lease `2026-10-05-lease-session-claude-executor-hardening.md` transformando o teste pontual do Claude em executor reutilizável, com saída JSON, timeouts, limpeza e validação por múltiplas tarefas.

## BASELINE_PROVEN
`2026-10-05-claude-hidden-profile-post-success.md`.

## Implementação
- Runner versionado em `ai-runners/claude_hidden_runner.py`.
- Aceita `--prompt`, `--prompt-file`, `--expect` e `--self-test`.
- Mantém perfil dedicado `claude-hidden-desktop-profile`.
- Chrome headful roda em desktop virtual oculto criado via Win32.
- Controle via CDP/Playwright.
- Retorna JSON com `ok`, `status`, `response`, `pid` e `elapsed_s`.
- Limpeza por árvore de PID no final.
- Python 3.13 recebeu somente o pacote Playwright; nenhum navegador extra foi baixado, pois o runner usa o Chrome instalado.

## Teste real
Self-test executado sequencialmente com três prompts independentes:
1. `Calcule 73 vezes 19. Responda apenas com o número.` => `1387`.
2. `Converta a palavra ANTHARES para letras minúsculas. Responda apenas com o resultado.` => `anthares`.
3. `Qual é a capital de Mato Grosso do Sul? Responda apenas com o nome da cidade.` => `Campo Grande`.

## Resultado
Saída consolidada:
`{"ok": true, "results": [{"ok": true, "status": "SUCCESS", "response": "Claude respondeu: 1387\n\n1387", "elapsed_s": 6.52}, {"ok": true, "status": "SUCCESS", "response": "Claude respondeu: anthares\n\nanthares", "elapsed_s": 6.65}, {"ok": true, "status": "SUCCESS", "response": "Claude respondeu: Campo Grande\n\nCampo Grande", "elapsed_s": 5.23}]}`

Tempo total do self-test: ~19 s.

## Evidência de limpeza
Após os três testes, `wmic` filtrado por `claude-hidden-desktop-profile` não encontrou Chrome residual; apareceu apenas o próprio comando de inspeção.

## Consequência
- PROVEN: o Claude já é um executor oculto reutilizável, não apenas um teste de eco.
- Novos chats/agentes devem usar `ai-runners/claude_hidden_runner.py` e preservar o perfil dedicado.
- Não voltar a headless puro ou ao Chrome normal sem mudança causal explícita.
- O lease de hardening está encerrado com sucesso.
