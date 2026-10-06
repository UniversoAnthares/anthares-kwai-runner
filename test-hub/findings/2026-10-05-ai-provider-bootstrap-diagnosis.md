# Bootstrap dos provedores IA: Perplexity/Gemini comprovados; Grok/Manus ainda sem sessão autenticada
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: test-hub/findings/2026-10-05-ai-provider-bootstrap-partial.md

## Objetivo
Validar, em perfis Chrome separados e desktops virtuais ocultos, se Grok, Manus, Perplexity e Gemini preservam autenticação e aceitam envio real sem tocar no Chrome normal do usuário.

## Baseline
- Claude já estava PROVEN em perfil isolado com resposta real.
- O usuário autorizou bootstrap visível, um provedor por vez, usando perfis dedicados.

## Testes
- Perfis dedicados criados para Grok, Manus, Perplexity e Gemini.
- Após o bootstrap visível, cada perfil foi reaberto em desktop virtual oculto.
- Prompt com marcador único enviado; sucesso exige o marcador aparecer uma segunda vez como resposta.

## Resultado
- Perplexity: PROVEN neste teste. `sent=true`, marcador apareceu 2 vezes, `SUCCESS`.
- Gemini: PROVEN neste teste. `sent=true`, marcador apareceu 2 vezes, `SUCCESS`.
- Grok: sessão não autenticada. Diagnóstico oculto mostra `Entrar`, `Criar conta` e `Inscreva-se para continuar`; o prompt foi aceito em modo visitante.
- Manus: sessão não autenticada. Diagnóstico oculto terminou em `https://manus.im/login?redirectUrl=%2Fapp%3Ffrom%3Dguest` com botões de login Google/Microsoft/Apple.

## Evidência decisiva
- Perplexity: `status=SUCCESS`, `count=2`.
- Gemini: `status=SUCCESS`, `count=2`.
- Grok: `title=Grok`, `marker_count=1`, texto visível inclui `Entrar`, `Criar conta`, `Inscreva-se para continuar`.
- Manus: `title=Login`, URL contém `/login`, `marker_count=0`.

## Consequência
- Considerar Perplexity e Gemini prontos para o runner oculto.
- Não considerar Grok/Manus autenticados só porque exibem uma caixa de prompt; ambos precisam de segundo bootstrap visível confirmado por estado de conta/avatar.
- Preservar perfis dedicados; não copiar cookies/tokens do Chrome normal.
