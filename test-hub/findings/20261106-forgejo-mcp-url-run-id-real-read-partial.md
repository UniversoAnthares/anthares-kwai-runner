# Forgejo MCP API paths and UI run mapping — verified live reads
STATUS: PARTIAL
AREA: forgejo-mcp-readonly
DATE_UTC: 2026-11-06T00:08:00Z
OWNER: chatgpt-aoi4-forgejo-api-20261106
SUPERSEDES: 20261106-lease-forgejo-mcp-api-paths-and-run-id.md
LEASE: CLOSED
BASE_HEAD: ba6ffe983a2112014db7926cf0bd6c39a1ea6061
SOURCE_COMMITS: c058ef948808ff230cd42a44bc1346190b0d6b85;59826d750839e985f4b9e53aebe1c8324e19a10a

## Objetivo
Consertar exclusivamente a ponte de leitura Forgejo implantada, preservando runners, segredos, publicação e OAuth existentes.

## Evidência real
A API Forgejo v15.0.9 em https://anthares.us/forgejo/api/v1/repos/anthares-admin/anthares-kwai-runner/actions/runs?limit=5 retornou HTTP 200. A mesma rota com `anthares-admin%2Fanthares-kwai-runner` retornou HTTP 404. A listagem indicou ID REST 567 para a execução exposta como #1 na URL da interface. A consulta GET /actions/runs/567 retornou HTTP 200; GET /actions/runs/1 retornou 404. O resultado da execução #1 continua `ci=failure`, `cd=skipped`. Endpoint jobs da versão instalada retornou 404 mesmo para ID REST válido; ausência de logs não comprova aprovação.

## Implementação
Patch mínimo: segmentos de `owner/repo` e subcaminhos de arquivos preservados; guarda de endpoints atualizada; timeout de 12 segundos; consulta de listagem resolves o número da interface para ID REST; indisponibilidade de jobs é reportada explicitamente. Os testes sintéticos da ponte foram ampliados com o caso #1->567 e as URLs sem %2F; 10 casos direcionados de regex conferidos em isolamento (10/10). Build/CI remoto do branch ainda requer verificação.

## Limites e consequência
Deploy em produção, OAuth `forgejo.read`, presença do segredo FORGEJO_READ_TOKEN e leitura autenticada de logs são UNVERIFIED. O patch não altera permissões, não obtém tokens nem contorna recusas administrativas. Não declarar item 4 DONE; CI/CD real precisa de CI e CD aprovados com recibo remoto. Pronta para PR e validação sem nova execução da workflow Forgejo.

COST: zero novos serviços ou pagamentos.
ROLLBACK: descartar PR; produção Cloudflare e runner preservados.
