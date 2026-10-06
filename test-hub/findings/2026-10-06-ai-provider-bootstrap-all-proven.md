# AI providers bootstrap: all five PROVEN
STATUS: PROVEN
AREA: session
DATE: 2026-10-06
LEASE: CLOSED
SUPERSEDES: 2026-10-05-ai-provider-bootstrap-partial-close.md

## Objetivo
Concluir e comprovar perfis isolados reutilizáveis para Claude, Grok, Manus, Perplexity e Gemini, sem tocar no Chrome normal do usuário.

## Resultado final
- Claude: PROVEN em finding anterior, com perfil persistente e envio oculto real.
- Grok: PROVEN. Após reautenticação manual no perfil dedicado, o diagnóstico oculto abriu conversa autenticada real em `https://grok.com/c/...`, enviou `DIAG_GROK_9167d7` e o marcador apareceu duas vezes no DOM (`marker_count=2`).
- Manus: PROVEN. Após restauração/autenticação manual da conta no perfil dedicado, o diagnóstico oculto abriu conversa real em `https://manus.im/app/...`, enviou `DIAG_MANUS_949179` e o marcador apareceu três vezes no DOM (`marker_count=3`).
- Perplexity: PROVEN. Teste determinístico anterior retornou `SUCCESS`, `count=2`.
- Gemini: PROVEN. Teste determinístico anterior retornou `SUCCESS`, `count=2`.

## Evidência final Grok
`{"provider":"grok","marker":"DIAG_GROK_9167d7","title":"Resposta exata DIAGGROK9167d7 - Grok","url":"https://grok.com/c/...","marker_count":2,"terms":[]}`

## Evidência final Manus
`{"provider":"manus","marker":"DIAG_MANUS_949179","title":"Reproduzir DIAG_MANUS_949179 - Manus","url":"https://manus.im/app/...","marker_count":3,"terms":[]}`

## Observações de harness
- Um teste do Manus falhou antes de abrir navegador por BOM UTF-8 (`U+FEFF`) ao carregar `diag_grok_manus.py`; relançado causalmente com `encoding='utf-8-sig'` e executado com sucesso.
- O estado anterior da conta Manus indicava conta excluída; o usuário concluiu manualmente restauração/autenticação e a sessão então persistiu.
- O incidente de disco cheio já havia sido resolvido removendo apenas cache descartável do pip.

## Estado consolidado
Todos os cinco provedores estão autenticados em perfis Chrome dedicados e foram comprovados por execução oculta sem uso do Chrome normal do usuário. Não há autenticação manual pendente neste escopo.
