# Anthares Studio — G3 pós-importação: integridade e REST em produção (somente leitura)
STATUS: PARTIAL
AREA: studio-g1-visual-staging
DATE: 2026-11-16
RUN: Hostinger PHP 8.3 / WordPress 7.1.4 / ACF ativo
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g3-readonly-audit-20261116
COMMIT: anthares-wordpress G3=ee480a823674318a5c55c07444505a4646930713 (16:50 UTC), live plugin PHP_SHA256=d29cb73bfbab555c904aaa07506d55943a1da533a0cc26ad37268cc479dbb8e9
SUPERSEDES: test-hub/findings/20261116-studio-g2-isolation-tests-pass-deploy-blocked.md

## Verificações observadas
- Entre 16:31 e 16:49 UTC, o ambiente foi modificado: `anthares-studio` 0.7.8-staging está **ativo**, e a página `/studio` (ID 21383) está **private**. HTTP anônimo em /studio respondeu 404, /estudio 200.
- Verificação posterior encontrou 71 pares `aest_* → anst_*`, com 40 publicados internamente e 31 na lixeira em ambos os lados. Mapeamentos `_anst_source_id`, `_anst_source_type`, `_anst_source_sha256`: 71 entradas únicas cada; 7 `_anst_delta` e 36 `_anst_project`; nenhuma referência órfã de projeto.
- Comparação SQL de 71 pares: **0 diferenças** de tipo, status, autor, título, conteúdo e menu_order. **7/7 Quill Delta iguais byte a byte**, sem divulgar material privado.
- Origem PHP SHA256 inalterado `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- `anst_writes_enabled=0` e `anst_trash_cleanup_enabled=0`. GET REST com administrador: 200; POST REST (canário sem escrita): 423; anônimo GET: 401; registros 71+71 antes/depois.
- GET REST de 2 autores de projetos ativos: 2 autorizações, zero falhas, **17 projetos idênticos por proveniência**, paridade de número e vínculo para projetos, notas, capítulos e cartões.
- `wp anst migrate` em dry-run com branch de QA `56efd039e328867171a7af0908932fca5f75b3c1`: SOURCE_COUNT=71, STATUS_publish=40, STATUS_trash=31, ALREADY_MAPPED=71; 4 categorias AUDIT_`*`=0; resultado DRY_RUN_ONLY.
- `python3 -m unittest discover -s anthares-studio/tests -v`: **15/15 PASS** no clone de teste; `php -l` plugin e migrador PASS; `qa/manifest-coverage-preflight.py --check`: **639/639**, exactly_once.
- WordPress `wp_scheduled_delete` está agendado em 2026-11-17 15:23 UTC, `EMPTY_TRASH_DAYS=30`; zero entradas ANST na lixeira com 30 dias ou mais.
- Código da proteção contra cron nativo e validação adicional de relações: PR https://github.com/UniversoAnthares/anthares-wordpress/pull/307 (DRAFT), **ainda não implantado**.
- Branch G3 `feat/studio-g3-migration-dryrun-20261116` sofreu commits concorrentes, incluindo zoom por usuário em `ee480a82`. Não sobrescrever/reforçar sem reconciliação.

## Limitações e gates
- Estado da importação atual foi **observado após** execução feita em outro fluxo; este finding registra QA de leitura, sem atribuir autoria da escrita nem presumir documentação do executor.
- G0 documentação: PROVEN; G1 backup e teste de restauração: PROVEN; G1 baseline visual completo: PARTIAL.
- G2 clone técnico ativo em piloto privado: PROVEN; G3 correspondência de posts/status/Delta: PROVEN por leitura, ciclo idempotente `--apply` no banco isolado ainda NÃO HOMOLOGADO.
- G4 API REST de leitura e permissão: PROVEN nos casos descritos; screenshots desktop/mobile e toda a matriz funcional: PENDENTE.
- G5 ACF em todos os campos, G6 navegação final, G7 requisitos 001–188, G8 lançamento: PENDENTES.
- HTML shortcode gerado para um proprietário contém raiz `anthares-estudio-root` com apenas um elemento; o front é renderizado no JS. Essa prova estrutural é limitada, sem substituir comparação visual.
- Dois testes isolados mais completos perderam stdout no canal remoto e deixaram o ambiente temporário limpo; não classificar como aceitação do `--apply`.

## Consequência
Preservar `/estudio` e seus 71 posts; manter `/studio` private e REST escrita OFF. Não ativar ACF/refatorações do clone até G4 e não implantar PR #307 sem reconciliação do head G3 e QA. Adquirir novo lease antes de qualquer escrita após a expiração do atual às 17:08 UTC. Registrar revisão do code hash, rollback e provas autenticadas de interface antes de liberar usuários.
