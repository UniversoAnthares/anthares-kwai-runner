# CORTES R07.6 — TikTok @lucasrosalem4: separação segura de credenciais e deploy

Status: **BLOQUEADO PARA CUTOVER**, controle de admissão em branch para revisão. Data: 24/10/2026. Não disparar publicação nem manipular dados, cookies, secrets, filas ou deployments enquanto os critérios abaixo não forem comprovados.

## Proprietário da conta e ativos

- Rede/conta: `tiktok/lucasrosalem4`; proprietário de referência do repositório: `UniversoAnthares`. Titular da sessão real: confirmar independentemente no TikTok Studio.
- Código consumidor: `tools/cortes_tiktok_lucasrosalem4_cloud_publish.py`; job principal `cortes-tiktok-lucasrosalem4-cloud-publisher.yml`; contingência `cortes-tiktok-lucasrosalem4-windows-fallback.yml`.
- Produtor: `UniversoAnthares/anthares-clipper` job `anthares-tiktok-owned-youtube.yml`.
- Fila/ledger: `infra/neon-cortes-lucasrosalem4/index.mjs`, tabela `cortes_tiktok_lucasrosalem4_publications`, identidade OIDC pelo repositório e workflow consumidor, lease e state STARTED/UNCERTAIN.
- Secret referenciado pelo consumidor (nome apenas): `TIKTOK_LUCASROSALEM4_STORAGE_STATE`; configurações Neon `DATABASE_URL` exclusivas do serviço requerem confirmação de IAM. O workflow produtor utiliza referências `WP_SITE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`, que **não** são segredos do consumidor.
- Kwai é **outra conta**: `kwai/lucasrosalem`, código e segredo `KWAI_PASSWORD`, Android primário, fila própria. Nunca credenciais, sessões, tarefas, ledgers, envs ou deployments intercambiáveis.

## Mudanças já realizadas nesta branch

1. `control_plane/persistent_publisher.py`: escrita de recibos exige `actor_network` e `state_root` tanto no nome legado quanto no novo alias; recusa ausência de argumentos, traversal e arquivos externos. Apenas diretórios preexistentes da própria rede são aceitos.
2. `test_persistent_publisher.py`: 10 testes positivos e negativos, inclusive Kwai → TikTok e TikTok → Kwai, aprovados em diretório descartável Windows. Isso **não** é uma fronteira de privilégio contra um agente que pode fornecer parâmetros falsos, alterar o módulo ou executar outras rotas.
3. `ci-hub/cortes_tiktok_lucas4_ownership.json`: matriz de proprietário e vínculos; campos de privilégios reais obrigatoriamente falsos.
4. `ci-hub/cortes_account_iam_audit.py`: avaliação do workflow, nomes de secrets permitidos, grupo de concorrência, conta, fila e OIDC. Condição atual `BLOCKED_PROVISIONING` por ausência de Environment vinculado. Todos os 11 testes aprovados.
5. `.github/workflows/cortes-tiktok-lucas4-iam-contract.yml`: regressão **sem secrets, sem OIDC, sem deploy, sem publicação, contents:read**. Enquanto o gate estiver na PR, nenhuma aprovação automática de produção decorre de um resultado verde.

## Migração segura para uma identidade real por conta — ordem obrigatória

1. **Provisão administrativa independente:** com o proprietário do repositório, criar Environment dedicado `cortes-tiktok-lucas4` no projeto consumidor, configurar aprovação de mantenedor distinto dos jobs consumidores e restrição de branch a uma referência protegida. Não permitir aos tokens de publicadores editar esse Environment, branch, secrets ou aprovação.
2. Provisionar a credencial `TIKTOK_LUCASROSALEM4_STORAGE_STATE` no Environment e validar a presença sem revelar valor. Não usar a mesma credencial para Kwai. Confirmar que somente os workflows/usuários especificamente aprovados alcançam a sessão.
3. Criar credencial de deploy/escopo mínimo distinta para o serviço e armazenamento/roles SQL exclusivos. `DATABASE_URL` precisa ter política Postgres/Neon que impeça UPDATE/DELETE/INSERT de outras redes, comprovada com credencial real. Uma role com acesso geral ao esquema não basta.
4. Adaptar **em PR separada de aplicação**, depois de IAM confirmado, os dois workflows existentes para referenciar explicitamente o Environment; preservar OIDC, concorrência e fencing. NÃO trocar controles de scheduling, URLs ou conta durante a mesma migração.
5. Executar a prova **DENIED**: job/identidade Kwai tenta acessar apenas recurso-teste pertencente ao TikTok e recebe 401/403/permission-denied; repetição simétrica TikTok → Kwai. Testar também leitura de secret, fila, DB, object storage, alteração de code path, branch e deploy. Identificar os principais por IDs/roles não administradores e registrar request IDs; nunca imprimir tokens.
6. Executar a prova **ALLOWED** com a identidade real TikTok para operação inofensiva e reversível no recurso-teste próprio; produção de post é desnecessária para testar ACL.
7. **Cutover conservador:** confirmar exclusividade do publicador, backups sob custódia segura e rollback; reconciliar trabalhos STARTED/UNCERTAIN, impedir dupla publicação; só então desabilitar/revogar a antiga referência de secret em nível de repositório. Não remover o segredo anterior antes da prova end-to-end e da capacidade de rollback.
8. Verificar contas de contingência Windows/Codeberg/GitHub e Cloudflare, impedindo bypass dos limites novos; revogar tokens gerais apenas depois de provar recuperação com least-privilege e aprovação do proprietário. Fazer registro do custo/cota e do SHA implantado.

## Motivos explícitos de não-promover SEC-02 e CORTES-ISO-06 hoje

- GitHub connected App não oferece mutação autorizada dos recursos de Environment/secret e/ou retorna 403 em políticas de branch do repositório privado; não executar o mesmo efeito por interface ou identidade alternativa para driblar a negativa.
- A equipe Vercel consultada apresenta somente identidade administrativa Owner; isto **não** prova permissão de deploy separada por conta. GitLab espelho protegido permite Owner push e tem CI bloqueado por quota; regras no repositório não tornam essa identidade de fato restrita.
- O workflow atual não tem `environment: cortes-tiktok-lucas4`. Adicionar apenas a linha YAML sem mover/revogar o segredo global **não** impede outros jobs do mesmo repositório de ler o secret.
- O Neon valida JWT assinado por workflow/repo, mas não há aqui recibo de cross-role denial com dois principals reais limitados. HTTP 401 para anônimo não satisfaz o teste bidirecional.
- Contas Windows que executam como `SISTEMA` têm acesso privilegiado e não comprovam separação de agentes. Não mudar as tarefas em execução sem identidade não administrativa provada.

**Aceite**: itens de governança documental/código podem ser preparados/testados isoladamente; a conclusão de segregação real exige controles administrativos em provedor e testes negativos por duas identidades efetivamente distintas. Toda revisão de PR é manual ou por autoridade independente.
