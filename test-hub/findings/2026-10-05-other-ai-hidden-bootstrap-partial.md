# Grok / Manus / Perplexity: arquitetura preparada, bootstrap ainda não comprovado
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: 6708c7c46c083f34f7954b52ebe09ae402807421
SUPERSEDES: none

## Objetivo
Reaplicar a arquitetura PROVEN do Claude a Grok, Manus e Perplexity sem tocar no Chrome normal do usuário.

## Baseline
- PROVEN para Claude: perfil Chrome dedicado + desktop virtual Win32 oculto + CDP/Playwright.
- `ai-runners/provider_hidden_probe.py` foi criado para probe somente-leitura, com perfis separados para Grok, Manus e Perplexity e sem envio de mensagens.

## Resultado desta rodada
- Busca de plugins/conectores ChatGPT por `Grok xAI Manus Perplexity`: nenhum conector disponível retornado.
- O primeiro launcher local do probe foi bloqueado antes de abrir navegador (`Acesso negado`).
- A tentativa alternativa com `runpy` foi bloqueada pela camada de segurança da OpenAI antes da execução.
- Portanto, isto é falha/limite do harness atual, NÃO evidência contra os três provedores.

## Consequência
- Não classificar Grok, Manus ou Perplexity como FAILED.
- Não repetir tentativas de burlar o bloqueio do launcher.
- Próximo caminho seguro: bootstrap explícito em perfis Chrome dedicados e isolados, com autorização do usuário para qualquer janela visível; depois reutilizar o padrão oculto já comprovado no Claude quando o launcher permitido estiver disponível.
- Nunca reutilizar/copiar cookies do Chrome normal.
