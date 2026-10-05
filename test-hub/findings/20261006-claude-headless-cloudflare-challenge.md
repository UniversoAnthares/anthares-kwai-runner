# Claude headless direto bloqueado por Cloudflare
STATUS: FAILED
AREA: session
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Testar em no máximo 30 segundos um envio mínimo ao Claude usando Chrome headless isolado, sem tocar no Chrome normal do usuário.

## Baseline
BASELINE_PROVEN: Chrome headless isolado inicia e encerra sem janela e sem processo residual.
FAILED_AVOIDED: não reutilizar Chrome visível, UIA, tabs, SendKeys ou perfil normal aberto.
SUCCESS_SIGNAL: campo de prompt acessível, envio de `Responda exatamente: TESTE_OK_CLAUDE` e resposta `TESTE_OK_CLAUDE`.
FAILURE_SIGNAL: login/challenge/bloqueio antes do campo de prompt ou timeout.
TEST_VALIDITY: processo deve encerrar em até 30 s e deixar RESIDUAL_COUNT=0.

## Resultado
O Chrome headless isolado abriu `https://claude.ai/new`, mas foi redirecionado para challenge do Cloudflare. Título observado: `Um momento.`. O campo de prompt não ficou disponível; nenhuma mensagem foi enviada.

## Evidência decisiva
Runtime total do harness: 8,60 s. Saída: `TITLE=Um momento.`, `RESULT=NO_PROMPT_BOX`, `RESIDUAL_COUNT=0`.

## Consequência
Não repetir o mesmo caminho de Chrome headless limpo + perfil temporário diretamente contra Claude sem uma mudança causal para lidar com o challenge/autenticação. O método é seguro quanto a isolamento/encerramento, mas não é suficiente para postar no Claude.
