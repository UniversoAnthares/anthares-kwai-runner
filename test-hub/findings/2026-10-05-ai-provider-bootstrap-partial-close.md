# AI providers: Claude/Grok/Perplexity/Gemini PROVEN; Manus reauth pending
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: 6f13292bcd671abdcc349474e5802c86fa81bcab
SUPERSEDES: none

## Objetivo
Fechar o bootstrap de perfis isolados para Claude, Grok, Manus, Perplexity e Gemini, reutilizando Chrome headful em desktop virtual separado sem tocar no Chrome normal do usuário.

## Baseline
- Claude já estava PROVEN com perfil persistente e envio oculto real.
- Grok/Manus/Perplexity/Gemini receberam perfis separados e bootstrap visível autorizado pelo usuário.

## Resultados confirmados
- Claude: PROVEN em finding anterior; envio oculto real confirmado.
- Perplexity: PROVEN. Teste determinístico enviou marcador exclusivo; o marcador apareceu duas vezes no DOM (`status=SUCCESS`, `count=2`).
- Gemini: PROVEN. Teste determinístico enviou marcador exclusivo; o marcador apareceu duas vezes no DOM (`status=SUCCESS`, `count=2`).
- Grok: PROVEN em 2026-10-06 após reautenticação real. Diagnóstico oculto abriu conversa autenticada, enviou `Responda exatamente: DIAG_GROK_9167d7`, recebeu `DIAG_GROK_9167d7`, contou duas ocorrências do marcador e não detectou termos de login/erro. URL final: `/c/cb61b3f2-9209-4c14-af55-bf64a859afc5?...`.
- Manus: ainda PENDENTE. O diagnóstico oculto continua abrindo `https://manus.im/login?redirectUrl=%2Fapp%3Ffrom%3Dguest`, título `Login`; novo bootstrap visível foi aberto em 2026-10-06 para autenticação manual.

## Evidência decisiva
- Perplexity: `{"provider":"perplexity","ok":true,"status":"SUCCESS","count":2}`.
- Gemini: `{"provider":"gemini","ok":true,"status":"SUCCESS","count":2}`.
- Grok pós-reauth: `marker_count=2`, resposta igual ao marcador, URL de conversa autenticada e `terms=[]`.
- Manus: título `Login`, URL `/login?redirectUrl=%2Fapp%3Ffrom%3Dguest`.

## Mudança causal implementada
`ai-runners/hidden_chat_runner.py` foi endurecido no commit `6f13292bcd671abdcc349474e5802c86fa81bcab`:
- adiciona Gemini;
- adiciona `--expect` para validação determinística por marcador em segunda ocorrência;
- separa `LOGIN_REQUIRED`, `NO_PROMPT_BOX`, `MARKER_TIMEOUT` e `SUCCESS`;
- preserva perfis dedicados e desktop virtual oculto.

## Incidente de harness resolvido
O disco C: chegou a 0 MB livres durante os testes. Foram removidos apenas caches descartáveis do pip; cerca de 9,9 GB foram liberados. Nenhum documento, projeto ou perfil autenticado foi apagado.

## Consequência
- NÃO repetir bootstrap de Claude, Grok, Perplexity ou Gemini.
- Manus é a única pendência deste conjunto: concluir login visível no perfil dedicado e depois validar ocultamente com marcador; só então marcar PROVEN.
- Não tratar presença de caixa de prompt como prova de autenticação: Grok permite prompt como visitante e Manus pode redirecionar para login após aparente sucesso.
- Não copiar cookies/tokens nem reutilizar o Chrome normal.
