# CF-03 / item 20 — lease de integração somente QA PR #1404
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1404
JOB: CF03-CLOSE-20261026
COMMIT: 0500ec1fbadb648bdd6b5bcc9fb90851a84ea50e
SUPERSEDES: none
LEASE_AREA: cf03-qa-pr1404-github-merge
LEASE_OWNER: ChatGPT-CF03-Closure
LEASE_BASE: github/main@00634f88955321cc94a3c480477a1001ff0b535d ; pr/head@0500ec1fbadb648bdd6b5bcc9fb90851a84ea50e ; gitlab/main@6f2bacc99fe1c24789b1b04db5c6721542db1977
LEASE_EXPIRES: 2026-10-26T12:36:17Z
LEASE_SCOPE: somente revisao de codigo, validacao estatica e tentativa governada de integracao de cinco arquivos de TEST HUB cf03 da PR #1404; sem implantacao de runtime/filas sociais; sem IAM, senha, token, plano, billing, dados ou publicacao. Sem modificar alteracoes locais existentes.

## BASELINE_PROVEN
Finding 20261025-cf03-queues-dlq-proven.md na PR, Cloudflare Queues/DLQ reais, redelivery idempotente e efeito unico no ledger, nenhuma rota de publicacao. GitHub PR em DRAFT e sem reviews, cinco arquivos exclusivos test-hub/findings e test-hub/fixtures/cf03. GitLab main contem historico independente, reconciliado sem force de main. Preflight local policy.py exit=0, versao f6fc9ca59a96e451; GitHub governance main versao 2e28d54043d6bad1 divergente; nao sincronizar cegamente.

## FAILED_AVOIDED
Nao reativar seed, segredo nem publicar no CORTES; nao alterar quaisquer filas produtivas; nao contornar gate de security/admin SEC-02 issue #30. Nao disparar deploy Cloudflare production usando alteracao de workflow. Nao tentar force push, substituir branch main, editar GitLab main, nem conceder privileges.

## SUCCESS_SIGNAL
Verificar sintaxe e hashes da fixture; executar aceite somente leitura do worker QA; PR pronta para revisao; se todos gates GitHub/concorrencia permitirem, merge normal/squash no GitHub sem modificar codigo produtivo, readback dos arquivos incorporados em main; producao preservada (health/version), GitLab historico preservado; Test Hub finding final. Se o GitHub exigir revisao/approval, nao contornar.

## FAILURE_SIGNAL
Conflito de HEAD, protecao de merge, falta de revisao requerida, lease alheio, sintaxe falha, push/main fora de escopo, GitLab merge destrutivo, alteracao do Worker produtivo ou integracao acidental de segredos. Encerrar como PARTIAL e manter PR em DRAFT ou pronta conforme controle.

## TEST_VALIDITY
Ficar em leitura para endpoints /health e /status existentes; verificacao Node --check e config Wrangler local na fixture. Testes reais de Queues/DLQ ja PROVEN no finding; sem replay de mensagens. Separar CI sem run de CI com SUCESSO; sem inferir implantacao produtiva a partir de merge.
