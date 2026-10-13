# Anthares Executor / Anthares-Reserva failover

Objetivo: retirar Cloudflare Browser Run e Render da posição de dependência obrigatória, preservando-os como fallbacks até prova real do executor próprio.

## Componentes próprios

- `anthares-executor/`: Chromium headless em contêiner, API autenticada, concorrência 1, prova de identidade e superfície de upload, perfil criptografado no GitLab.
- `anthares-reserva/`: roteador de provedores com ledger, geração/fencing, idempotência e circuit breaker. Seleciona apenas um provedor por job e não faz failover depois de um envio cujo resultado possa ser ambíguo.
- GitLab `browser-state`: persistência externa criptografada do perfil; nenhum cookie/token em claro no Git.
- GitHub/Codeberg/GitLab: redundância do código. Codeberg já recebe os pushes da branch por mirror.

## Matriz operacional

| Provedor | Papel | Estado | Promoção |
| --- | --- | --- | --- |
| Anthares Executor em GitHub Actions | executor Docker efêmero | QA em implantação | pode virar executor sob demanda após QA verde |
| GitLab CI | executor efêmero secundário | branch preparada; runner ainda não comprovado | somente após job real verde |
| Codeberg | espelho / candidato a runner | espelhamento comprovado; runner não comprovado | não promover sem runner real |
| Cloudflare Browser Run | fallback sob demanda | Chromium real comprovado; rate limit 429 observado | manter como fallback de baixa frequência |
| Render | fallback persistente | restore/checkpoint de perfil comprovado | manter até autenticação e upload serem comprovados fora dele |
| Browserless | fallback futuro | cota gratuita atual esgotada | reavaliar somente após reset, sem upgrade pago |

## Regras

1. Custo obrigatório: R$ 0; sem cartão, billing ou upgrade pago.
2. PC do usuário nunca é runner/executor de nuvem.
3. Publicação real permanece desativada até `identity_verified=true` e `upload_surface_verified=true` numa sessão legítima.
4. `job_id` é idempotente e `generation` impede execução por geração antiga.
5. Nunca enviar o mesmo job a dois provedores. Falha de transporte após dispatch é `ambiguous`, não motivo para reenvio automático.
6. Secrets ficam apenas nos cofres dos provedores. Não entram no repositório, logs ou chat.
7. Perfil Chromium é restaurado antes da execução e checkpointado somente após o Chromium parar.

## Gate para substituir Cloudflare/Render

A promoção do executor próprio exige, nesta ordem:

1. Docker build e `/ready` verdes em runner remoto.
2. autenticação da API rejeitando chamada sem bearer token.
3. navegação real no Kwai em probe somente leitura.
4. restauração do snapshot criptografado em executor diferente do Render.
5. `identity_verified=true` para a conta esperada.
6. `upload_surface_verified=true` no Studio.
7. ciclo de restart + restore repetido sem perda de sessão.
8. somente depois disso habilitar uma operação de publicação, sempre com lease/fencing e dedupe.

Enquanto qualquer gate estiver vermelho, Cloudflare e Render permanecem fallbacks e nenhuma publicação automática é liberada.
