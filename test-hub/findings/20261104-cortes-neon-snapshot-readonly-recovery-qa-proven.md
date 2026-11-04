# AOI 21 / CORTES — recuperação de snapshot Neon read-only homologada em QA isolada
STATUS: PARTIAL
AREA: architecture
DATE: 2026-11-04
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/232
JOB: ChatGPT isolated Python QA, no GitHub Actions run
COMMIT: 52987aed165f3682ef6c5f5ec0774b76bad94893
SUPERSEDES: 20261103-lease-architecture-cortes-neon-snapshot-readonly-restore.md
LEASE_CLOSED_UTC: 2026-11-04T03:20:57.521Z
GOVERNANCE_MANIFEST: 223433740e807a90
ITEMS: [21]
COST_ADDED: 0

## Objetivo
Provar compatibilidade de recuperação do checkpoint remoto de CORTES sem executar publicador, alterar tabelas de produção, acionar PC pessoal ou repetir GitHub Actions. Reaproveitar a tabela existente e o leitor já implantado, preservando a PR concorrente #229 de CAS/writer.

## Feito e evidenciado
- PR privada Clipper #232 merge normal condicionado a HEAD em 2026-11-04: SHA 52987aed165f3682ef6c5f5ec0774b76bad94893. Adiciona apenas qa/cortes_neon_snapshot_restore_readonly.py (blob SHA 5f4031fd9c791be9b377f337bb0dbb068c3dbb22) e tests/test_cortes_neon_snapshot_restore_readonly.py (blob SHA b4c09642a0334a62957867ceadaaae191ec76f66).
- O código permite somente dois SELECT parametrizados, com revisão/digest/tamanho fixos em cada read. Aceita endpoint Neon controlado, bloqueia redirect e escrita, 5 MiB máximo, responde apenas com resumo e hash. A CLI exige Linux GitHub-hosted, flag explícita CORTES_LEDGER_REMOTE_READ_ENABLED=1, secret previamente autorizado e RUNNER_TEMP. Não existe job scheduler nem consumidor novo nesta PR.
- Os dois arquivos materializados no ambiente efêmero de QA tinham SHA Git de blob EXATAMENTE igual ao branch e ao main. py_compile PASS e Python unittest 9/9 PASS, inclusive restauração sintética pelo leitor real qa.cortes_short_resume_guard.read_ledger_snapshot e limpeza do scratch, corrupção de SHA, Base64 inválido, chunk ausente, revisão divergente/inválida, tamanho excessivo e hostname remoto rejeitado.
- Neon SELECT real (somente leitura): revisão 15399, digest cc5d1a188b53f6f1780f392097b73ea0ac78758b632dd6205e9890ad37d2206a, source_bytes 2932006. O comando de chunk substring/encode retornou 4096 bytes codificados em 5464 caracteres Base64 válidos, pinado pela revisão+SHA+tamanho.
- Prova anterior: snapshots rev 15399 e 14688 íntegros, cinco fontes no último, 68/68 segmentos UNCERTAIN do Kwai com IDs/intervalos correspondentes, 68/68 arquivos MP4 WordPress disponíveis. Não há recibo externo Kwai para os 68.
- PR #229 de ledger CAS de outro agente continua DRAFT e foi preservada sem escrita. PR #190 de Drive/mídia também preservada.

## Limitação / critério terminal
- O teste completo de download dos 2932006 bytes e parsing no GitHub-hosted real NÃO ocorreu: não foi possível verificar quota Actions pelo endpoint autorizado, e a credencial CORTES_NEON_DATABASE_URL e flag não foram provisionadas/ativadas. Sem quota comprovada, não disparar novo CI, não criar segredo ou nova execução para "provar".
- O leitor já é DEPLOYED como código somente de QA, sem scheduler, triggers, PC ou serviço novo; não representa publicador em produção nem migração dos jobs daily/resume.
- Os 68 registros Kwai continuam RECONCILE_REQUIRED; verificador de atestação independente ainda em PR #2057 draft e não há prova do post no Kwai. Nenhuma linha/estado foi alterado.
- A restituição funcional completa da fonte para daily/resume ainda exige backup de masters, quota, ownership e fencing comprovados, e a PR #229 CAS não pode ser confundida com o esquema atualmente ativo.
- Rollback: PR de reversão estrita dos dois arquivos do commit 52987aed, após verificação de SHA. Nenhum dado de produção a reverter.

## Estado por subcritério
PROVEN: integridade base64 de chunk Neon, SHA remoto já conhecido, algoritmo read-only em QA sintética, compatibilidade do parser e limpeza.
DEPLOYED: ferramenta de QA no main Clipper, gate não ativado.
UNVERIFIED: restauração integral do blob em runner GitHub-hosted; publicação Kwai efetiva; retirada total de Windows.
RECONCILE_REQUIRED: 68 tentativas Kwai e três confirmadas históricas sem remote_id.
Lease encerrado por este finding. Nova intervenção de produção exige lease e quota observada.
