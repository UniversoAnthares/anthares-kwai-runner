# ARA sem dependência de Render — estado e implantação

## Confirmado em produção (13/10/2026)
- Controle durável ativo: `https://anthares-ara-backup.anthares1.workers.dev`.
- Gateway MCP/OAuth ativo: `https://anthares-ara-mcp.anthares1.workers.dev/mcp`.
- Agente Windows canônico: `DESKTOP-FTDK0HP`, executado como SYSTEM em sessão 0, sem desktop interativo.
- O supervisor canônico usa Cloudflare como caminho primário e não contém Render entre os controles normais.
- O controle persiste estado em Cloudflare Durable Objects/SQLite, com criação, deduplicação, lease e armazenamento de resultado aprovados no `/_selftest`.
- O gateway MCP possui Durable Object próprio para chave Ed25519 e estado OAuth.
- O gateway chama o controle por Cloudflare Worker service binding `ARA_CONTROL`, não pela rede pública e não por Render.
- A chave pública do gateway Cloudflare foi fixada no controle, junto das chaves legadas para janela de migração; a implantação usa chaves fixadas antes de qualquer descoberta legada.
- Comando real anterior `echo CLOUDFLARE-ARA-OK` concluiu pelo controle Cloudflare com exit code 0.

## Prova de implantação independente
Workflow: `Cloudflare ARA Render Independence`, run `38409222503`, commit `803a2fd8951926d0f97c3c6953646b49d30783fe`.

O run concluiu com sucesso todas as etapas:
1. validou fontes e bindings;
2. compilou o cliente MCP usando `env.ARA_CONTROL.fetch`;
3. executou dry-run do Wrangler;
4. implantou `anthares-ara-mcp`;
5. fixou as chaves públicas confiáveis no controle;
6. implantou `anthares-ara-backup` com verificação baseada em chaves fixadas;
7. comprovou `/healthz` com `independent_of_render_postgres=true`;
8. comprovou `/_selftest` com `create`, `idempotency`, `lease` e `result` verdadeiros;
9. comprovou o gateway MCP com `ok=true`, `render_independent=true`, `control_ready=true` e `device_connected=true`;
10. comprovou metadata OAuth e rejeição HTTP 401 de MCP sem autenticação.

Marcador final da execução: `RENDER_INDEPENDENT_CLOUDFLARE_STACK_OK=1`.

Versões implantadas nesse teste:
- `anthares-ara-mcp`: `b6b53017-db10-4a4a-afc3-4dc217d6485c`.
- `anthares-ara-backup`: `c2c3d78b-3b67-4751-b56c-cda263301931`.

## Dependência restante fora da infraestrutura
A infraestrutura e o dispositivo já possuem caminho funcional sem Render. O conector/app Anthares Remote atualmente cadastrado na conta do ChatGPT ainda aponta para o gateway MCP antigo. Trocar ou criar um app MCP no ChatGPT é uma ação da conta do usuário e exige conexão/autorização explícita na interface do ChatGPT; não existe uma credencial administrativa do ChatGPT armazenada no repositório que deva contornar essa etapa.

Endpoint a cadastrar no ChatGPT:
`https://anthares-ara-mcp.anthares1.workers.dev/mcp`

O gateway implementa OAuth com PKCE, access token, refresh token e aprovação vinculada ao computador autorizado. Durante a conexão, o código de aprovação é enviado ao clipboard do dispositivo por meio do ARA; o usuário informa esse código na página de autorização. Depois da conexão, validar `session_status` e uma operação inócua antes de retirar o conector antigo.

## Render após a migração
- Não contratar plano pago.
- Não depender do PostgreSQL Render para estado do ARA.
- Não apagar serviços Render antes da troca do conector ChatGPT: eles podem permanecer ociosos como legado até expiração gratuita.
- A conclusão operacional é definida pelo uso do novo conector Cloudflare em uma conversa real, não pela existência dos serviços antigos.

## Restrições permanentes
- Custo R$ 0; sem cartão, cobrança ou plano pago.
- Não usar o PC como runner de CI, publicação ou fallback de serviços.
- Não abrir janelas no desktop interativo; administração Windows roda em SYSTEM/sessão 0.
- Não declarar o conector ChatGPT migrado antes de a conexão OAuth ser concluída na conta.
