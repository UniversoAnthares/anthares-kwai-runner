# CF-02 R07.6 item 19 — GitHub CAS real HTTP409 recovered without production deploy
STATUS: PROVEN
AREA: github, cloudflare
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40319550329
JOB: 121560741631
COMMIT: 00634f88955321cc94a3c480477a1001ff0b535d
SUPERSEDES: test-hub/findings/20261026-cf02-real-provider-cas-running.md
LEASE_AREA: cf02-github-cas-provider-qa-isolated-20261026
LEASE_OWNER: ChatGPT-CF02-CAS
LEASE_STATUS: CLOSED

## Objetivo e estado produtivo
Integrar a correção CAS após HTTP409 em .github/workflows/cloudflare-central-deploy.yml e provar a operação real da API GitHub, sem efetuar deploy Cloudflare, alterar o recibo de produção ou publicar conteúdo.
PR #1346 (https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1346) promovida de draft para READY, merge normal pelo conector GitHub com aprovação explícita do titular; squash commit 00634f88955321cc94a3c480477a1001ff0b535d. Título de merge com [skip ci] para impedir acionamento automático da rotina de deploy Cloudflare e endpoint de maintenance Kwai. O GitHub main foi relido: workflow blob 04029a3fc0622189d0f936d90ac0129fc2cf8d44, testes CAS blob edbc62771118bdd1a37de24c3e8c43382621feff, workflow QA blob 5c48bb57be02b3f18634262238e0d849f705d5f3; todos integrados.
Antes: workflow main blob aa844d0cd740a27ba8724c2004179fee952f0d32 com PUT único, corrida real no run #40151702008 (deploy e health bem-sucedidos, etapa de salvar recibo FAILED com 409). Teste não implantante da PR #1346 havia passado no run #40157117628. Current /main production receipt original permanece blob SHA 47faf493a965be52cf57ea8780cc61f68510567f e checked_at_utc=2026-10-19T23:45:51.943051+00:00 após merge + QA, sem falso recibo.

## Teste REAL de comparação e troca no provedor
Branch exclusiva evidence/cf02-real-provider-cas-qa-20261026; workflow QA .github/workflows/cf02-real-provider-cas-qa.yml possui trigger push SOMENTE dessa branch e paths somente do próprio arquivo; permissions contents:write somente job QA; não lê secret Cloudflare, não tem deploy, não chama publicador.
O QA extrai o bloco inline Python do NOVO workflow principal commit 00634f8, modifica apenas path do recibo de QA e branch GET/PUT para a branch exclusiva (mantenha a origem main inalterada), cria arquivo sintético QA, injeta concorrência REAL com API REST PUT sobre MESMO arquivo após GET original, provocando 409. O código original capturou o HTTP409, releu SHA do arquivo alvo na mesma branch e efetuou PUT na segunda tentativa.
EVIDÊNCIA DECISIVA: GitHub Actions #40319550329/job #121560741631 COMPLETED SUCCESS, etapa 'Force a REAL provider HTTP409 and prove original CAS receipt retry' SUCCESS. Readback GitHub em test-hub/fixtures/cf02/live-cas-qa-evidence-v4.json, blob 96c459211331d04d9fd2f6808c1330a105ef06dc: provider_http409_observed=true; retried_with_fresh_sha=true; total_original_receipt_put_attempts=2; original_script_saved=true; cloudflare_deploy=false; production_receipt_touched=false; publisher_mutation=false. Recibo sintético em live-cas-qa-receipt-v4.json, blob a8675f40ee0dd9b105b8a51184e28a1dc67b40e8: control_version='cf02-cas-live-qa-synthetic', deploy_outcome='success', control_healthy=true. Estes dados NÃO são recibo de deploy real.
Runs #40318473908, #40318806356 e #40318947798 deram FAILURE por erro do HARNESS (GET SHA ainda apontava '?ref=main' enquanto PUT apontava QA branch); 422 Invalid request portanto foi erro de teste que não atingiu a pré-condição 'conflito real com SHA enviado'. Foram classificados INVALID/NOT_TESTED para a hipótese 422 produtiva, não como defeito do CAS em main. Corrigido o caminho GET para a mesma branch no run #40319550329, mantendo o código de deploy intacto.
Nenhum upgrade/custo, segredo social, binding, cron, fila, publicação, SQL, reenvio UNCERTAIN, maintenace Kwai ou Worker produtivo alterado no ensaio. A correção de 409 em main está INTEGRADA/TESTADA em API REAL, mas o fluxo E2E de deploy + recibo produtivo aguarda release governada com filas e estados reconciliados. CF-02 item 19 segue concluído no pacote autônomo de 1 Worker staging/rollback por PR #1402; demais Workers e IAM de outras redes continuam controles independentes.

## Segurança/continuidade
Governança GitHub manifest main 2e28d54043d6bad1 vs Windows local f6fc9ca59a96e451 divergentes; preflight ARA CF02-RELEASE-20261026 exit0, Windows runner worktree com 17 entradas dirty preservadas. Política CI: merge [skip ci] mantém prova PR CI #40157117628 e não deve disparar deploy por push. Retomar deploy somente com gate de manutenção, locks, filas, estado UNCERTAIN reconciliados e rollback do Worker produtivo planejado. Nenhum agente pode presumir que o merge atestou uma nova versão Cloudflare.
