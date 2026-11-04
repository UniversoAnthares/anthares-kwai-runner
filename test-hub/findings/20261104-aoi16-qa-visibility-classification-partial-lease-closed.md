# AOI #16 — infra QA separada das falhas reais de publicação
STATUS: PARTIAL
AREA: qa-p0-visibility-classification
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T17:40:08.289Z
ITEMS: [16]
LEASE_AREA: qa-p0-visibility-classification
LEASE: CLOSED
LEASE_OWNER: chatgpt-optimization-20261104
SUPERSEDES: 20261104-lease-qa-p0-visibility-separation.md
GOVERNANCE_MANIFEST: 223433740e807a90
PREVIOUS_MAIN: 11a1703c037b69afc78308ad70f8bcfd7f06330d
BRANCH_PATCH_HEAD: bc33f49f7371727bfa051d9ea9d9058f127c397b
RUN: node none; local Python syntax and behavioral fixture
JOB: none
COST_ADDED: 0

## Problema comprovado
Os Issues GitHub #2045 e #2028 estão abertos e trazem stage qa_visibility_lost_github_repo, causados por leitura inacessível de Actions no repositório secundário. Título antigo Falha de publicação e label publication-failure atribuíam origem errada; perda de visibilidade não comprova falha de envio.

## Correção e escopo
A função existente create_issue no tools/cortes_qa_p0_router.py agora separa stage que começa por qa_visibility_lost_. Os alertas continuam abertos como QA-P0 com título de infraestrutura e instrução de recuperar visibilidade/quota/permissões. Os incidentes reais de publicação conservam título, label publication-failure, proteção de fila, dedupe, reconciliação e idempotência. Nenhum acionamento ou agendamento foi criado.
Blob da função corrigida em branch: 5fac1d649fb39df7ca5ec29d6814faecfc8de779; testes em branch: 5825b58f7c94559c677889a9dd0dadb2c87622e5.
QA isolado em Python, trecho de função reconstruído da revisão exata, com 4/4 testes PASS: visibilidade GitHub, visibilidade WordPress, publicador verdadeiro, fingerprint. Os dois novos testes foram adicionados à suíte do repositório, ainda sem rodar no CI. Sem usar Actions, Cloudflare ou PC do titular.
PR alheia #547 modifica as regras de fila presa em outra faixa de linhas; sua branch permanece intacta e precisará rebase apropriado pelo owner se for integrada.

## Estado real
Item #16 permanece PARTIAL: múltiplos incidentes reais [QA P0] ainda abertos; preservar causas, sem fechá-los por aparência. Após merge, alterar a categorização dos Issues de visibilidade antigos somente se comprovada correspondência do fingerprint; não apagar dados. Custo adicional zero.
Rollback: revert do commit isolado, preservando os issues; restabelecer classificação anterior se o comportamento real discordar.