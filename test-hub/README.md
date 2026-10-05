# Anthares Test Hub

Fonte compartilhada de verdade para testes, decisões e falhas do projeto Anthares remoto.

## Regra obrigatória para qualquer chat/agente

1. Antes de propor, alterar ou repetir um teste, leia este arquivo e os registros relevantes em `test-hub/findings/`.
2. Não repita uma estratégia marcada `FAILED` sem uma mudança explícita que ataque a causa registrada.
3. Não substitua uma estratégia `PROVEN` por hipótese não testada.
4. Ao terminar um teste, crie um NOVO arquivo em `test-hub/findings/`; não edite registros históricos.
5. Se um resultado antigo deixar de valer, crie outro registro com `SUPERSEDES:` apontando para o anterior.
6. Nunca grave secrets, cookies, tokens, senhas ou dados de sessão aqui.
7. Evidência vale mais que descrição: registrar run/job/commit e a linha decisiva do log.

## Estados

- PROVEN: comprovado em teste real.
- FAILED: executado e falhou; não repetir sem alteração causal.
- PARTIAL: parte comprovada, conclusão ainda não.
- RUNNING: teste disparado, sem resultado final.
- SUPERSEDED: registro substituído por evidência posterior.
- ABANDONED: caminho descartado por decisão arquitetural.

## Formato de cada finding

```
# título
STATUS: PROVEN|FAILED|PARTIAL|RUNNING|SUPERSEDED|ABANDONED
AREA: android|kwai|tiktok|cloudflare|github|live|session|architecture
DATE: YYYY-MM-DD
RUN: URL ou none
JOB: URL/id ou none
COMMIT: sha ou none
SUPERSEDES: arquivo ou none

## Objetivo
...

## Resultado
...

## Evidência decisiva
...

## Consequência
O que os próximos chats DEVEM ou NÃO DEVEM fazer.
```

## Estado consolidado atual

- PROVEN: repositório público `UniversoAnthares/anthares-kwai-runner` recebe GitHub-hosted runners sem depender da cota do repositório privado.
- PROVEN: vault público validado; `PRIVATE_REPO_TOKEN` não faz parte da arquitetura final.
- PROVEN: Android API 35 x86_64 anuncia arm64-v8a e `libndk_translation.so`.
- PROVEN: conjunto de splits Kwai: base + `dfm_ug` + `config.arm64_v8a` + `config.xxhdpi`; instala e chega a `KWAI_LAUNCHED`.
- FAILED: autologin anterior procurou login antes de atravessar permissão/onboarding; retornou RC=3.
- FAILED: matrix de 10 probes do run 37372686273 não testou as hipóteses: heredoc Python foi quebrado pelo executor em comandos shell (`import: not found`). Não interpretar esses jobs como resultado das estratégias.
- RUNNING: matrix corrigida usa `kwai_onboarding_probe.py`, run 37377433515.
- ABANDONED: PC como executor/fallback; Oracle; Open Platform Kuaishou como publicador do Kwai brasileiro; Aurora/Play Store como aquisição principal.

## Concorrência

O diretório `findings/` é append-only de propósito. Chats simultâneos devem criar arquivos únicos no padrão:

`YYYYMMDD-HHMM-area-resumo-curto.md`

Se dois chats trabalharem simultaneamente, ambos podem acrescentar evidência sem disputar um arquivo central. Este README é um índice/protocolo e só deve ser atualizado quando uma decisão consolidada mudar.
