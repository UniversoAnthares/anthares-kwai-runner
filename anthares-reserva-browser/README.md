# Anthares-Reserva Browser

Navegador de contingência sob demanda, independente do Render, implementado sobre Cloudflare Browser Run.

## Estado e limites

- Código versionado; implantação em Cloudflare e teste real **não comprovados**.
- `GET /health` verifica apenas o Worker e não requer token.
- `GET /_selftest`, `GET /_auth_selftest` e `POST /probe` exigem `Authorization: Bearer <token>`.
- `/_auth_selftest` exige cápsula de autenticação e chave privada provisionadas como secrets; sem elas falha de forma segura.
- Sessão Kwai autenticada, upload e publicação real **não comprovados**. Nunca confundir cookie importado com autenticação confirmada.
- Cloudflare Browser Run Free tem cota de uso, portanto não substitui Chromium contínuo nem publicação em escala.
- Não utilizar o PC do usuário como executor e não contratar serviços pagos.

## Implantação

Provisionar em Cloudflare Workers com Browser Run habilitado, a partir da pasta `anthares-reserva-browser`. Configurar o secret `ANTHARES_RESERVA_TOKEN` no próprio painel Cloudflare; não gravá-lo no Git nem compartilhá-lo no chat. Para verificação autenticada, configurar também os secrets `RESERVA_MIGRATION_PRIVATE_KEY` e `RESERVA_KWAI_CAPSULE` por canal seguro e autorizado.

Depois da implantação, verificar `/health`, confirmar HTTP 401 nos endpoints de teste sem token e realizar `/_selftest` com token. Somente então testar `/_auth_selftest` com cápsula legítima, sem imprimir cookies ou tokens. Não promover para produção sem evidência real de identidade e capacidade de upload.

## Segurança operacional

Não desativar o Render até que o novo executor demonstre recuperação de estado, autenticação Kwai, execução real, proteção de segredos, limites de recursos e rollback. O controle de fila deve preservar lease único e fencing para impedir publicações duplicadas.
