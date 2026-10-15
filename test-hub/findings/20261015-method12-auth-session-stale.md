# Método 1+2 — sessão YouTube remota está presente, mas expirada
STATUS: FAILED
AREA: session
DATE: 2026-10-15
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38824417685
JOB: 116728391766
COMMIT: 0eb34e2c7242df150ac964ac4ecedd4085640862
SUPERSEDES: none

## Objetivo
Retomar o teste prático do método 1+2 após a recuperação do Anthares Remote, usando o fluxo autenticado já implementado para o vídeo `9CIk-I_3VhM`, intervalo `8–98`.

## Baseline comprovado
- Anthares Remote respondeu com `connected=true` no backend canônico Vercel+Neon.
- `MEmu_4` está `Running`; no contexto interativo do usuário `Lucas`, o ADB nativo na porta `5038` enxerga `127.0.0.1:21543` como `device`.
- O workflow recebeu `YOUTUBE_COOKIES` e materializou o arquivo privado, portanto o secret remoto existe.

## Resultado
O teste parou antes do Método 1. A etapa `Prove authenticated metadata first` falhou porque o YouTube declarou os cookies fornecidos inválidos/rotacionados e devolveu `Sign in to confirm you’re not a bot`.

O task local `Anthares-YouTube-Cookie-Refresh-Once` foi executado novamente, mas seu log local terminou em `Could not copy Chrome cookie database`; portanto não há prova de que um novo conjunto de cookies válidos tenha sido gerado. O código de saída da tarefa do Windows não deve ser usado como prova de autenticação.

## Evidência decisiva
Run `38824417685`:
- `METHOD12_AUTH_SECRET=PRESENT`;
- `METHOD12_COOKIE_FILE=READY`;
- warning: `The provided YouTube account cookies are no longer valid`;
- erro: `Sign in to confirm you’re not a bot`.

Runtime local:
- `Anthares-MEmu4-User-Probe`: `127.0.0.1:21543 device` via ADB `-P 5038` no contexto de `Lucas`;
- `youtube-auth-proof.log`: `ERROR: Could not copy Chrome cookie database`.

## Consequência
Não repetir o workflow `cortes-method12-authenticated-media-once.yml` com o secret atual. Antes de novo run, é necessária uma mudança causal no caminho de autenticação: renovar a sessão de forma segura sem depender da cópia bloqueada do banco de cookies aberto do Chrome, ou substituir essa fronteira por outro mecanismo autenticado comprovado. Não transportar nem registrar cookies/tokens em findings ou logs.

O Método 2 não foi executado neste run; publicação social permaneceu `false`.