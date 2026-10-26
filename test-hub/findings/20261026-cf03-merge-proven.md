# CF-03 / item fixo 20 — integração QA PR #1404 comprovada, lease encerrado
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1404
JOB: CF03-CLOSE-20261026
COMMIT: 4919848fc5a793f4276fe5b131192464f2353f8b
SUPERSEDES: test-hub/findings/20261026-cf03-merge-lease.md
LEASE_AREA: cf03-qa-pr1404-github-merge
LEASE_OWNER: ChatGPT-CF03-Closure
LEASE_STATUS: CLOSED

## Objetivo
Integrar a fonte QA verificada sem acionar ou alterar publicadores reais, respeitando preflight, lease e integridade.

## Resultado comprovado
- Preflight local policy.py da operacao CF03-CLOSE-20261026 PASS (exit 0). A copia local governance f6fc9ca59a96e451 difere da main Github governance 2e28d54043d6bad1; nenhuma sincronizacao ou sobrescrita executada.
- Lease da operacao registrado por update_ref CAS no commit dfb61d3c9496d76e91f97bb633587f62faffd3f2 da PR e verificado na branch.
- Worker fonte recuperado da PR e validado por Node --check PASS; SHA256 33A9113A6F448E028D374E1AF0CF5A08487F5EB7F44409A665F250D2C8731BBC. Config QA contém somente Queue, DLQ e DO independentes; temporarios locais removidos.
- Teste de leitura real Cloudflare via ARA: CF03_LIVE_ACCEPTANCE=PASS; status do ledger seeds=1, effects=2 unicos, deadletter=1, attempts 1/2/2. Nenhuma nova mensagem enviada.
- PR 1404 promovida de DRAFT para READY, merge SQUASH autorizado por GitHub: SHA 4919848fc5a793f4276fe5b131192464f2353f8b. Readback PR merged=true; main tem worker e lease QA.
- Depois do merge, ARA leitura: CF03_POSTMERGE_LIVE=PASS, producao anthares-control/health ok=true, version=2026-10-17-physical-android-v18, CF03_EFFECTS=2, CF03_DLQ=1.
- PR restrita a test-hub/fixtures/cf03 e test-hub/findings. Nao houve migracao de filas produtivas, nao houve IAM/segredos ou endpoints sociais conectados. Billing global nao auditado nesta operacao.

## Resultado de espelho e limites
- GitLab main possuia historico proprio reconciliado antes do merge. A incorporacao de 4919848 em GitLab nao foi atestada no momento do merge; verificar por ancestralidade/arquivo posteriormente. Nao forcar sincronizacao nem conflitar com agente de espelhos.
- Item CF-03 autonomo PROVEN; pendencias de SEC-02 (issue https://github.com/UniversoAnthares/anthares-governance/issues/30), ISO-04, ledger canonico/UNCERTAIN, permissionamento por rede e rollout produtivo sao controles independentes e NAO foram dados como concluidos. Bloqueio anterior de seguranca para credenciais exige liberacao oficial do administrador, nao uso de fallback para reproduzir a recusa.
- Sem publicacao/cutover, nem contratacao de plano. Preservar ambos os IDs de filas QA como evidencia historica; nao resemear os mesmos eventos.
