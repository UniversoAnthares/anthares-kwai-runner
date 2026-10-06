# AI orchestrator + Anthares production runtime PROVEN
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-06
RUN: 37419903193
JOB: a7bfb88a81c715a9 (HARNESS failure before provider load; superseded by direct in-process validation)
COMMIT: 44c0d51af48c90f4cf3e8150965cf2113938cf72
SUPERSEDES: test-hub/findings/2026-10-06-lease-ai-orchestrator-integration.md
LEASE: CLOSED

## Objetivo concluído
Consolidar Claude, Grok, Gemini, Perplexity e Manus em uma única interface local com fallback/healthcheck/logs; provar os cinco com tarefas reais; integrar o mesmo contrato semântico ao Anthares; e separar definitivamente a camada local-web do runtime cloud de produção independente do PC.

## Implementação local
- `ai-runners/anthares_ai.py` é a CLI única.
- `--provider auto|claude|grok|gemini|perplexity|manus`.
- Ordem padrão: Claude -> Grok -> Gemini -> Perplexity -> Manus.
- Suporta `--order`, `--exclude`, retries, timeouts, healthcheck, logs JSONL sem prompt/resposta/secrets e falha simulada para teste de fallback.
- Saída padronizada: `ok`, `provider`, `status`, `response`, `runtime=local-web`, `attempts`, `elapsed_s`.
- Os runners de baixo nível permanecem isolados por perfil Chrome e desktop Win32 oculto; Chrome normal não é tocado.
- O orquestrador invoca os runners no mesmo processo Python para evitar restrição de subprocesso aninhado do harness remoto.

## Validade / correções causais
1. Primeira bateria via AI Commander job terminou antes de abrir qualquer provedor com `PermissionError: [WinError 5] Acesso negado` ao tentar Python -> Python. Classificação: HARNESS. Correção: runners importados/invocados in-process.
2. O primeiro envelope continha cada marcador duas vezes no próprio prompt, permitindo falso positivo. Correção: cada marcador aparece exatamente uma vez no prompt; teste unitário impede regressão.
3. Perplexity inicialmente ecoou `[sua resposta]`. Correção: removido placeholder literal do envelope.
4. Perplexity depois expôs par de marcadores aninhado. Correção: extrator avalia pares, remove marcadores aninhados/placeholders e só aceita conteúdo não vazio.
5. Após as correções, Perplexity devolveu exatamente `PERPLEXITY_FIX_OK`.

## Testes automatizados
- `py_compile`: PASS para orchestrator e runners.
- `python -m unittest -v test_anthares_ai.py`: 8/8 PASS.
- GitHub Actions `AI runners contract tests`: run `37419903193`, conclusão `success` no commit `44c0d51...`.

## Bateria real dos cinco provedores
Healthcheck final, todos com resposta real delimitada e marcador esperado:
- Claude: SUCCESS, resposta `HEALTH_CLAUDE_037049af`.
- Grok: SUCCESS, resposta `HEALTH_GROK_c32fc43d`.
- Gemini: SUCCESS, resposta `HEALTH_GEMINI_acb3da55`.
- Perplexity: SUCCESS, resposta `HEALTH_PERPLEXITY_38b68941`.
- Manus: SUCCESS, resposta `HEALTH_MANUS_1396c2e6`.
Resultado agregado: `ok=true`, `status=SUCCESS`.

## Bateria funcional com prompts diferentes
- Claude: `29 * 31` -> `899` PASS.
- Grok: `ANTHARES` em minúsculas -> `anthares` PASS.
- Gemini: capital de Mato Grosso do Sul -> `Campo Grande` PASS.
- Perplexity: mês após setembro -> `Outubro` PASS (comparação case-insensitive com `outubro`).
- Manus: `144 + 56` -> `200` PASS.
Resultado: 5/5.

## Fallback comprovado
Execução `--provider auto --simulate-failure claude --prompt 'Responda exatamente: FALLBACK_OK'`:
- tentativa 1 Claude: `SIMULATED_FAILURE` (falha controlada; sessão não foi quebrada);
- tentativa seguinte Grok: `SUCCESS`, resposta `FALLBACK_OK`.
Resultado agregado: `ok=true`, provider `grok`.

## Integração Anthares / produção
`anthares-ai-hub` foi elevado ao contrato 1.9.4 e o estado ativo em produção foi verificado.
- `Anthares_AI_Runtime_Contract` adiciona `ok`, `status`, `response`, `runtime`, `pc_required`, `attempts` sem remover `text`, `provider`, `model`, `usage`.
- `anthares_ai_request_contract()` sempre retorna array normalizado, inclusive em falha.
- `anthares_ai_runtime_status()` reporta apenas provedores atualmente `available`.
- Consumidores existentes de `anthares_ai_request()` recebem os campos novos pelo filtro `anthares_ai_result` sem mudança de API antiga.
- PHP lint 8.3: PASS para arquivo principal do Hub e runtime contract.

## Prova no-PC / cloud real
WP-CLI padrão do host estava ligado a PHP 7.4 e falhava porque o tema exige PHP >= 8.0. Isso era HARNESS do CLI, não falha do site/Hub. Os testes válidos foram executados explicitamente com `/opt/alt/php83/usr/bin/php`.

`anthares_ai_runtime_status()` em Hostinger retornou:
- `ok=true`
- `status=READY`
- `runtime=cloud`
- `pc_required=false`
- disponíveis: `gemini`, `groq`, `cloudflare`, `openrouter`, `mistral`, `nvidia`, `huggingface`.

Requisição real executada dentro do WordPress/Hostinger por `anthares_ai_request_contract()`:
- prompt de prova: `CLOUD_RUNTIME_OK`
- `ok=true`, `status=SUCCESS`
- provider: `gemini`
- `runtime=cloud`
- `pc_required=false`
- response: `CLOUD_RUNTIME_OK`.

Compatibilidade da API histórica também provada em produção via `anthares_ai_request()`:
- `text=LEGACY_COMPAT_OK`
- `response=LEGACY_COMPAT_OK`
- `runtime=cloud`
- `pc_required=false`
- provider `gemini`.

## Arquitetura consolidada
- Local web runners: desenvolvimento, diagnóstico e operação assistida; dependem do PC e dos perfis dedicados.
- Produção Anthares: `anthares-ai-hub` no Hostinger, exclusivamente provedores cloud; não chama navegador local nem depende do PC.
- Falha de todos os provedores cloud retorna erro/`ALL_FAILED`; não há fallback oculto para o PC.
- A única exceção geral já consolidada para dependência do PC continua sendo a parte YouTube do Clipper; esta implementação de IA não cria nova exceção.

## Resultado
Os seis itens do plano estão concluídos. Não resta bootstrap, integração, fallback ou separação cloud/local pendente neste escopo.
