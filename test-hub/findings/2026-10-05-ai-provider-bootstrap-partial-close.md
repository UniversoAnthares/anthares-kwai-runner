# AI providers: Claude/Perplexity/Gemini PROVEN; Grok reauth awaiting validation; Manus reauth pending
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
- Perplexity: PROVEN neste ciclo. Teste determinístico enviou marcador exclusivo; o marcador apareceu duas vezes no DOM (`status=SUCCESS`, `count=2`).
- Gemini: PROVEN neste ciclo. Teste determinístico enviou marcador exclusivo; o marcador apareceu duas vezes no DOM (`status=SUCCESS`, `count=2`).
- Grok: o primeiro suposto bootstrap era falso positivo. Diagnóstico posterior abriu `https://grok.com/` como visitante e mostrou `Entrar`, `Criar conta` e `Inscreva-se gratuitamente`. O usuário então reabriu o perfil dedicado e confirmou manualmente que estava vendo a conta/avatar sem `Entrar / Criar conta`. A validação oculta pós-reauth NÃO foi executada porque a cota mensal do Remote Desktop Commander terminou exatamente nesse ponto.
- Manus: o primeiro suposto bootstrap também era falso positivo. Diagnóstico posterior abriu `https://manus.im/login?redirectUrl=%2Fapp%3Ffrom%3Dguest`, título `Login`, com botões de autenticação; portanto precisa de novo bootstrap visível antes da prova oculta.

## Evidência decisiva
- Perplexity: `{"provider":"perplexity","ok":true,"status":"SUCCESS","count":2}`.
- Gemini: `{"provider":"gemini","ok":true,"status":"SUCCESS","count":2}`.
- Grok antes da reauth: título `Grok`, URL `https://grok.com/`, termos `Entrar/Criar conta`, marcador apenas uma vez.
- Manus: título `Login`, URL `/login?redirectUrl=%2Fapp%3Ffrom%3Dguest`.
- Após o usuário corrigir manualmente o Grok, o executor remoto reportou cota mensal esgotada e instruiu a não repetir/reconectar; o device permanece pareado.

## Mudança causal implementada
`ai-runners/hidden_chat_runner.py` foi endurecido no commit `6f13292bcd671abdcc349474e5802c86fa81bcab`:
- adiciona Gemini;
- adiciona `--expect` para validação determinística por marcador em segunda ocorrência;
- separa `LOGIN_REQUIRED`, `NO_PROMPT_BOX`, `MARKER_TIMEOUT` e `SUCCESS`;
- preserva perfis dedicados e desktop virtual oculto.

## Incidente de harness resolvido
O disco C: chegou a 0 MB livres durante os testes. Foram removidos apenas caches descartáveis do pip; cerca de 9,9 GB foram liberados. Nenhum documento, projeto ou perfil autenticado foi apagado.

## Consequência
- NÃO repetir bootstrap de Claude, Perplexity ou Gemini.
- Quando o Remote Desktop Commander voltar, primeira ação: fechar a janela isolada do Grok se ainda estiver aberta e validar `grok` com `hidden_chat_runner.py --expect <marcador>`; se SUCCESS, marcar PROVEN.
- Depois abrir Manus no mesmo perfil dedicado, autenticar de fato e validar com marcador; só então marcar PROVEN.
- Não tratar presença de caixa de prompt como prova de autenticação: Grok permite prompt como visitante e Manus pode redirecionar para login após aparente sucesso.
- Não copiar cookies/tokens nem reutilizar o Chrome normal.
