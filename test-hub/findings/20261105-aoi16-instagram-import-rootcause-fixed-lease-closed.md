# AOI #16 — Instagram: corrigir import de módulo que derrubou dois publicadores em QA
STATUS: PARTIAL
AREA: qa-p0-instagram-import-failure-41258536427
DATE_UTC: 2026-11-05T01:25:40.533Z
ITEMS: [16]
LEASE_OWNER: chatgpt-aoi16-20261105
LEASE: CLOSED
SUPERSEDES: lease-20261105-aoi16-instagram-import-p0.md
BASE_HEAD: bd6610036568a4f4399b4d621e64f3d05800f961
SOURCE_BLOB_BEFORE: 0c675d1fb4754b0df6e0a76d32f93ee9fc0e6a93
SOURCE_BLOB_AFTER: d1fcd28950310b2732ddbdb5bc1e7f345a3cb432
TEST_BLOB_BEFORE: 5ad4605c8a550d7719b5b5d9ed12265e6fd0b657
TEST_BLOB_AFTER: e509dcc851673c17bfd3f17a655ae5f367b8d340
PEER_BASELINE: GitLab project 87307248 / main content blob SHA identical to GitHub pre-patch for both files.
COST_ADDED: 0
LIVE_PUBLICATION: NONE
PROVIDER_WORKFLOW_STATE: disabled_manually

## Causa real e evidências
- 2026-10-31 run 41222737930, job 124600496645, em publish: `ModuleNotFoundError: No module named 'instagram_publish'`, disparado por `from scripts.instagram_autopublish import load_ledger, save_ledger` no inline script da workflow `instagram-auto-10day.yml`. Incidente P0 #2027 relaciona essa execução.
- 2026-11-01 run 41258536427, job 124706765819, erro idêntico, referente ao P0 #2044.
- O módulo real existe em `scripts/instagram_publish.py`. `scripts/instagram_autopublish.py` importava `instagram_publish` sem o namespace `scripts`; quando o consumidor importava pelo namespace, o Python procurava o módulo na raiz, onde ele inexiste.
- Patch mínimo: `from scripts.instagram_publish import InstagramAPIError, client_from_env`. `scripts/instagram_autopublish.py` já inclui a raiz do repositório no `sys.path` para suportar execução direta. Nenhuma chamada de rede ou rotina de publicação foi alterada.
- Teste de regressão `test_repository_root_package_import_in_clean_process` executa import package em Python `-I`, cwd raiz, subinterpretador com path explícito, sem rede nem credenciais. Evita mascarar o erro anterior pelo `sys.path` da suíte antiga.

## QA executado e limites
- QA isolado executado em container independente do Windows do usuário: duas provas do mecanismo de import com a estrutura correspondente (`scripts/`): import corrigido retorna 0; antigo falha com `ModuleNotFoundError`. **Este teste comprova a resolução do mecanismo, e não representa a execução da suíte completa do repositório**.
- Novo teste de regressão foi instalado no teste offline existente, pendente de execução integral quando um executor externo elegível estiver disponível. Workflow `instagram-auto-10day.yml` permanece `disabled_manually`.
- Não foi enviada qualquer mídia nem iniciado job GitHub. O P0 permanece aberto até run real seguro e prova da publicação remota ou terminal `NOT_APPLIED`.
- Os outros incidentes Instagram Graph preflight HTTP/auth e publicadores de rede possuem causas independentes; #16 global permanece PARTIAL.

## Próximo gate
Com elegibilidade de quota externa e autorização da fila: executar exclusivamente QA de import/contratos sem disparo de publicador, verificar P0 #2027 e #2044, preservar histórico de mídia não confirmada. Nunca reativar workflow ou publicar por causa de uma correção de import. Arquivos alterados apenas scripts/instagram_autopublish.py e test-hub/test_instagram_autopublish.py.
