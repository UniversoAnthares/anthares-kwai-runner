# Lease: AI orchestrator + Anthares integration
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
LEASE_EXPIRES: 2026-10-06T02:00:00-04:00

## Objetivo
Consolidar Claude, Grok, Manus, Perplexity e Gemini em executor único com fallback/healthcheck/logs; validar em bateria real; integrar a um ponto real do Anthares; e separar explicitamente runtime local de caminho cloud/no-PC.

## BASELINE_PROVEN
- `2026-10-06-ai-provider-bootstrap-all-proven.md`: os cinco provedores autenticados em perfis dedicados e comprovados por execução oculta.
- `hidden_chat_runner.py` já suporta Grok/Manus/Perplexity/Gemini; Claude tem runner próprio PROVEN.
- Regra arquitetural Anthares vigente: runtime geral não pode depender do PC; PC pode ser console/desenvolvimento e a única exceção previamente aceita é a parte YouTube do Clipper.

## FAILED_AVOIDED
- Não tocar no Chrome normal do usuário.
- Não considerar presença de caixa de prompt como prova de autenticação.
- Não usar pure headless para bootstrap quando provedores bloqueiam/challenge.
- Não substituir runners PROVEN antes de uma camada de orquestração validada.
- Não declarar cloud/no-PC PROVEN sem execução fora do perfil local.

## SUCCESS_SIGNAL
1. CLI única aceita `--provider <nome|auto>` e devolve JSON padronizado.
2. `auto` executa fallback determinístico e registra tentativas/latência/status sem expor secrets.
3. Healthcheck e retries/timeout são testáveis e cobertos por testes locais.
4. Bateria real produz respostas válidas de todos os cinco provedores e prova fallback com pelo menos uma falha controlada.
5. Existe integração Anthares concreta e reversível usando contrato estável do orquestrador.
6. Caminho no-PC fica implementado/validado onde tecnicamente possível; qualquer dependência externa inevitável fica separada e explicitamente fail-closed, sem fingir equivalência com os perfis locais.

## FAILURE_SIGNAL
- Sessão de provedor deixa de persistir; runner toca Chrome normal; fallback mascara falha como sucesso; integração quebra fluxo existente; ou caminho cloud é declarado funcional sem prova independente.

## TEST_VALIDITY
- Erro de Python/Playwright/launcher/quoting antes da página carregar é HARNESS, não falha do provedor.
- Teste real de provedor exige URL autenticada + prompt enviado + resposta observável específica.
- Teste no-PC exige execução em ambiente remoto/cloud; teste no PC não conta.
