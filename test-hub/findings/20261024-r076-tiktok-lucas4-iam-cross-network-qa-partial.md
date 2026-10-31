# R07.6 — Evidência técnica dos itens 02, 05, 07, 08 (TikTok lucasrosalem4)
STATUS: PARTIAL (02 concluído por matriz; 05 gate em draft; 07 e 08 não autorizados em produção)
AREA: architecture / security
DATE: 2026-10-24
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40140618358
JOB: r076-cortes-tiktok-lucas4-iam-boundaries
COMMIT: 6d6a78b2daf628bae4e7c3ccd282f031e086fc76
SUPERSEDES: test-hub/findings/20261024-cortes-iso01-iso02-inventory-and-fenced-receipts.md

## Base canônica e mudanças
- Governança f6fc9ca59a96e451, auditoria 218/0. Fonte principal de propriedade da conta em Google Drive: https://docs.google.com/document/d/14-vikhVVc6R-63Wk8DDHObo2_aUaiNzXP4gGEB3lvf4/edit
- Branch `platform/cortes-tiktok-lucas4-account-fence-20261024`; PR draft #1332; main, publicadores, CI produtivo, Neon, Cloudflare, Vercel e secrets inalterados.
- `control_plane/persistent_publisher.py`: chamador legado não aceita mais escrita sem actor_network/state_root; restringe diretório, nome, receipt.platform, traversal e symlink antes do replace.
- `ci-hub/cortes_account_iam_audit.py`: verifica vínculo da conta, workflows, referência de segredo própria, claims da função Neon, controle de concorrência e permissões mínimas. Nenhum segredo é lido. Fail-closed `BLOCKED_PROVISIONING` até ambiente dedicado e IAM independentes.
- `ci-hub/cortes_tiktok_lucas4_ownership.json`: contract metadata apenas, campos externos de autorização obrigatoriamente false. Runbook de migração e rollback separado.

## Testes executados
- Windows/Anthares Remote: 10 testes do gravador de recibos passaram em filesystem descartável; DENIED Kwai→TikTok e TikTok→Kwai, DENIED recibo estrangeiro, traversal, ausência de diretório e chamada sem escopo; ALLOWED gravações próprias.
- Windows/Anthares Remote: 11 testes do auditor de IAM/secret/CI, PASS; detecta ambiente inexistente nas DUAS rotas correntes, mantém deploy_authorized=false. Sem acesso a token real.
- GitHub Actions PR run `40140618358`: SUCCESS, job `121011402827`, 10 + 11 testes PASS, validação final de bloqueio de aprovisionamento PASS. Test runner sem secrets, sem id-token, sem deployments nem publicações.
- GitHub Actions Control Plane run `40140618328`: SUCCESS; job `121011401457` passou validação e regressões; não certifica IAM.
- Guard canônico do `UniversoAnthares/anthares-clipper` versão blob `751a75f120efa7e70e2b1aa2489b36a0e11085cf`: 23 unit tests PASS no Windows; 6 verificações dirigidas adicionais PASS: Kwai próprio ALLOWED, TikTok contra Kwai DENIED, rename negado; simetricamente TikTok próprio ALLOWED, Kwai contra TikTok DENIED, rename negado. O teste inicial adicional falhou por quoting em PowerShell e foi corrigido/reexecutado, nenhum arquivo produtivo tocado.
- Execução REAL consumidora anterior à PR: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40133241857; log job 120989266807: `SECONDARY_CLOUD_IDENTITY_VERIFIED account=lucasrosalem4 existing=5`, `SECONDARY_CLOUD_IRREVERSIBLE_FENCE=1`, `SECONDARY_CLOUD_CONFIRMED=https://www.tiktok.com/@lucasrosalem4/video/7700345607579389205`. Esta prova cobre ALLOWED no fluxo existente, não DENIED de outro agente.

## Bloqueios comprovados
- O Github App conectado não concede provisão/restrição de secrets de repo/Environment ou proteção obrigatória de main via ferramenta disponível; API do repositório privado clipper devolveu 403 nas leituras de proteção. Não contornar recusa por outro controller.
- O segredo `TIKTOK_LUCASROSALEM4_STORAGE_STATE` ainda é referenciado por workflow SEM `environment: cortes-tiktok-lucas4`, e o fallback repete o padrão. Escopo de valor real UNKNOWN. Não transferir/revogar credencial sem custody e rollback.
- Vercel team tem um único Owner; GitLab espelho tem um único Owner com can_push=true. Não existem aqui duas identidades externas não-administrativas vinculadas às contas, nem prova de cross-access DENIED.
- Script path gate em CI não é ACL de OS nem IAM da provedora. Os usuários Windows SISTEMA/Lucas não garantem isolamento. Blob SHA em PR não garante promoção bloqueada por pessoa distinta.
- Repositório Google/Neon consultado não fornece autoridade provada para a função específica cortestiktok4 em outra conta; não alterar projeto Neon aleatório como substituto.
- Teste reversível live de duas identidades/segredos/deploys e teste do caminho recovery ainda exigidos antes de migrar produção. Não fazer publicação de teste para validar IAM.

## Ação de promoção (DONO/ADMIN)
1. Prover Environment próprio com approver independente e token somente por rede; distribuir segredo no scope correcto e confirmar custódia e rollback.
2. Restringir GitHub branch/deploy e tokens de agents não-admin; dividir as roles de producer/consumer/fallback e revogar acesso cross-network.
3. Executar ALLOWED na própria rede e DENIED no TikTok por Kwai, DENIED no Kwai por TikTok com identidades verdadeiras; repetir para fila, DB, estado, secret, Git e deploy. Registrar request IDs sem conteúdo sensível.
4. Somente depois aplicar PR de workflows de produção e revogar segredo global; liberar a promoção. Até isso: PR #1332 fica draft, itens 05/07/08 ficam PARCIAIS. Não realizar merge/deploy automático.
