# Claude headless: matriz de acesso e postagem
STATUS: FAILED
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Testar postagem mínima no Claude (`Responda exatamente: TESTE_OK_CLAUDE`) usando apenas navegadores headless isolados, sem tocar no Chrome normal do usuário.

## Baseline e validade
BASELINE_PROVEN: Chrome headless isolado consegue iniciar e encerrar sem criar janela visível.
FAILED_AVOIDED: não reutilizar Chrome visível, não usar tabs do perfil normal, não usar foco/SendKeys, não copiar cookies/credenciais.
SUCCESS_SIGNAL: campo de mensagem disponível em sessão autenticada + envio do prompt + presença de `TESTE_OK_CLAUDE` na resposta.
FAILURE_SIGNAL: challenge Cloudflare persistente ou login obrigatório antes do campo de mensagem.
TEST_VALIDITY: cada probe roda em processo isolado; resultado só vale se título/URL/DOM forem lidos e o processo terminar. Travamento de harness não conta contra a hipótese.

## Métodos executados
1. Playwright + Chrome headless + perfil dedicado persistente: 22.0 s -> título `Um momento…`, 0 campos de mensagem, Cloudflare challenge.
2. Reabertura do mesmo perfil persistente: 21.3 s -> mesmo resultado; persistência não resolveu o challenge.
3. Playwright + Chrome headless efêmero: 16.6 s -> `Um momento…`, 0 campos, Cloudflare challenge.
4. Playwright Chromium bundled: 19.1 s -> `Just a moment...`, 0 campos; mesma tela de challenge (o harness classificou como NO_PROMPT_BOX por string de detecção incompleta, mas o título é evidência direta do challenge).
5. Chrome headless nativo, sem Playwright, controlado via DevTools Protocol/CDP: 16.36 s -> `Um momento…`, 0 campos, Cloudflare challenge.
6. Busca de plugin/conector `Claude Anthropic`: nenhum plugin disponível retornado.

## Resultado
Nenhuma mensagem foi enviada. Quatro arquiteturas headless distintas convergiram para o challenge do Cloudflare antes da UI do Claude. O bloqueio não é específico do Playwright nem do uso de perfil persistente.

Um runner multiprobe anterior travou e foi encerrado; por isso esse travamento é INVALID como evidência sobre Claude. Após a matriz, houve um processo Chrome residual do probe CDP; ele foi encerrado pelo PID e uma nova varredura confirmou zero processos dos perfis/scripts de teste.

## Evidência decisiva
Títulos observados: `Um momento…` / `Just a moment...`; `box_count=0` em todos os probes válidos; nenhum `TESTE_OK_CLAUDE` enviado ou recebido.

## Consequência
Próximos chats NÃO devem repetir Chrome headless Playwright persistente/efêmero, Chromium Playwright ou Chrome headless CDP esperando que apenas trocar a biblioteca resolva o acesso. Para avançar, é necessária uma mudança causal real, por exemplo integração oficial/API autenticada ou um perfil headless dedicado legitimamente autenticado por um fluxo suportado. Não copiar cookies/credenciais do perfil normal nem voltar a controlar abas visíveis.
