# CORTES — isolamento de filas por rede e contrato legado WordPress
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-23
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/185
JOB: Anthares Remote Windows / Python 3.12 offline synthetic regression
COMMIT: 5ae097cd3d4fea1b2e4a8fcf858f30276628ca9f
SUPERSEDES: test-hub/findings/20261023-cortes-three-independent-social-adapters-partial.md

## Objetivo
Preparar separação de fila, ledger, lease/fencing e credenciais por rede
sem interferir na autoridade atual do WordPress Video Distributor.

## Resultado
ci/network_queue_broker.py: protótipo offline com base SQLite separada
por network/account; fila com idempotência ligada aos hashes de mídia e
transcrição, claim exclusivo, token de lock persistido somente em hash,
lease_generation e confirmação com evidência vinculada aos hashes.
Expiração e resultados incertos NÃO reinserem na fila automaticamente.
Respostas brutas das APIs não são persistidas como erro/confirmation.
SQLite connections agora fechadas explicitamente; causa corrigida após
falha inicial de exclusão de arquivos temporários no Windows.

ci/network_legacy_claim_contract.py: contrato somente leitura que valida
provider/account/queue_id/lock_token/lease_generation, credenciais
específicas e proof de vídeo/legenda. Não chama WordPress nem envia
nenhuma publicação.

PRs #186 (Threads), #187 (Instagram), #188 (X): workflow YAML de QA
somente workflow_dispatch, contents:read e nenhum segredo. Configuração
PyYAML validada no Windows. Cinco arquivos por PR, todos aceitos
pelo guard de escopo de rede.

## Evidência decisiva
Windows/Python 3.12: test_network_queue_broker.py 26 PASS;
test_network_legacy_claim_contract.py 17 PASS. Total 43 PASS.
Corrida entre dois workers comprovou uma única posse do mesmo item.
Cross-platform claim com o mesmo queue_id rejeitado.
Confirmation mismatched transcript/media SHA256 rejeitada.
Provider exception com string sensível rejeitada do ledger.
Workflows por plataforma YAML_VALID, manual_only, read_only, no_secrets.
PR scopes accepted: approved-paths:threads / instagram / x.

## Consequência
STATUS PARTIAL, todas as PRs draft e não implantadas.
Queue real: WordPress Anthares Video Distributor. O protótipo SQLite
não deve ser ligado como segunda fonte de publicação.
Os contratos legados observados não comprovam ainda approved_caption,
transcript_sha256 e media_sha256 em cada claim. Novo gate bloqueia
até esses campos serem fornecidos e verificados editorialmente.
Continuam pendentes identidade Windows/ACL, token por rede, integração
dos lançadores, filas/ledgers reais, migração sem duplicação e release gate.
