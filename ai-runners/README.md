# AI runners

Executores locais de desenvolvimento para serviços web de IA usando perfis Chrome dedicados e isolados.

## Orquestrador único

`anthares_ai.py` é a entrada recomendada para Claude, Grok, Gemini, Perplexity e Manus.

Exemplos:

```powershell
py -3.13 anthares_ai.py --provider auto --prompt "Resuma este parágrafo em uma frase."
py -3.13 anthares_ai.py --provider grok --prompt "Calcule 73 vezes 19."
py -3.13 anthares_ai.py --health
```

Recursos:

- `--provider auto|claude|grok|gemini|perplexity|manus`
- ordem de fallback configurável com `--order`
- exclusões com `--exclude`
- retries controlados com `--retries`
- timeouts separados de carregamento/resposta
- healthcheck real por provedor
- logs JSONL sem prompt, resposta, cookies ou credenciais
- `--simulate-failure` para prova controlada de fallback
- saída JSON padronizada: `ok`, `provider`, `status`, `response`, `runtime`, `attempts`, `elapsed_s`

O orquestrador usa envelopes de resposta com marcadores descartáveis para extrair apenas o conteúdo útil e não depende de seletores frágeis de texto da interface.

## Runners de baixo nível

`claude_hidden_runner.py` é o runner PROVEN dedicado ao Claude.

`hidden_chat_runner.py` cobre Grok, Manus, Perplexity e Gemini e aceita `--expect` + `--expect-end` para delimitar a resposta.

Todos:

- usam perfil Chrome dedicado;
- executam Chrome headful em desktop virtual Win32 oculto;
- controlam a janela via CDP/Playwright;
- não reutilizam, leem nem copiam cookies do Chrome normal;
- encerram somente a árvore do Chrome isolado criada pela execução.

## Produção / no-PC

Estes runners são uma camada local de desenvolvimento, diagnóstico e operação assistida. O WordPress de produção não deve chamá-los e não deve depender do PC do usuário.

O runtime de produção permanece no `anthares-ai-hub`, executado no servidor WordPress com provedores cloud. O Hub expõe `anthares_ai_request_contract()` e `anthares_ai_runtime_status()` com `runtime=cloud` e `pc_required=false`. Assim o contrato de resposta é comum, enquanto os ambientes permanecem fisicamente separados.

## Testes

Suíte unitária:

```powershell
py -3.13 -m unittest -v test_anthares_ai.py
```

Bateria real dos cinco provedores:

```powershell
py -3.13 anthares_ai.py --health
```

Fallback controlado, sem quebrar sessão de nenhum provedor:

```powershell
py -3.13 anthares_ai.py --provider auto --simulate-failure claude --prompt "Responda apenas: FALLBACK_OK"
```

## Regra de segurança

Não apontar estes runners para o perfil Chrome normal do usuário. Cada provedor deve usar perfil dedicado. Se uma sessão expirar, o bootstrap de autenticação deve usar o fluxo oficial do provedor; não copiar cookies/sessões do navegador normal.
