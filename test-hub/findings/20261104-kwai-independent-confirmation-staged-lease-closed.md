# CORTES/Kwai — confirmação com atestação independente protegida em PR de QA
STATUS: PARTIAL
AREA: queue
DATE: 2026-11-04
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2057
JOB: isolated JS with synthetic HMAC, no Actions run
COMMIT: f7da4eeb27c53b46acefd7c6ae0f806ab8a1692c
SUPERSEDES: 20261104-lease-queue-kwai-independent-confirmation.md
LEASE_CLOSED_UTC: 2026-11-04T02:53:37.387Z
GOVERNANCE_MANIFEST: 223433740e807a90
ITEMS: [AOI-21]
PRODUCTION_STATUS: UNCHANGED
COST_ADDED: 0

## Causa e correção STAGED
- O contrato kwai-confirm da função Neon em PR draft #2057 aceitava uma URL Kwai, método e identidade informados pelo próprio publicador. O formato do URL não demonstrava consulta externa independente.
- Corrigido em infra/neon-cortes-queue/index.mjs: exige atestação HMAC-SHA256 de verificador separado, com chave dedicada via variável de ambiente CORTES_KWAI_INDEPENDENT_ATTESTATION_KEY (nenhuma chave foi criada ou incluída no código). Vincula job ID, lease_generation, conta, destino, ID remoto, URL pública, método, identidade de mídia e carimbo UTC com idade máxima de 10 minutos. Com ausência de chave ou assinatura, confirmação falha fechada.
- Aplicada comparação de digest com timingSafeEqual; HMAC bruto é removido da evidência gravada. UPDATE permanece com CAS de status started, lease_owner, lease_generation e media_sha256.
- kwai-uncertain-read restrito ao workflow específico kwai-publisher; o papel probe de outros alvos foi removido do acesso aos registros Kwai.
- Cinco testes Node foram adicionados em tests/cortes_kwai_independent_attestation.test.mjs, preparados, ainda sem execução CI/Node com crypto real. A assinatura criptográfica real e integração do verificador independente ainda precisam de homologação.

## Validação independente desta intervenção
- Syntax parse JavaScript do módulo após patch: PASS.
- Sete testes de fluxo executados no contrato real extraído em ambiente JS isolado com HMAC SINTÉTICO, Buffer e URL simulados: 7/7 PASS. Cobriram leitura de papel genérico, ausência de chave, assinatura inválida, atestação expirada, geração errada, ID público diferente e avanço para SQL com CAS e supressão da assinatura. Esta prova é exclusivamente da lógica e dos gates, não valida criptografia real Node, rede pública ou banco.
- Nenhuma alteração a Neon, Workers Cloudflare, workflows acionados, credenciais, scheduler, mídia ou fila de produção.

## Evidência do estado externo
- Neon kwai:lucasrosalem: 456 confirmed e 68 uncertain. Os 68 carecem de remote_id; três dos 456 confirmed também carecem de remote_id, apesar de evidência de confirmação existente; exigir validação específica sem mutação automática.
- Em auditoria anterior desta data, os 68 URLs WordPress responderam HTTP 200/video/mp4 por HEAD e o ledger Neon revisão 15399 coincidiu em tamanho/SHA256 com a cópia original.
- O acesso ao perfil Kwai não apresentou os recibos públicos exigidos; Browserless Free sem unidades remanescentes e TinyFish sem saldo gratuito. Nenhuma compra ou bypass de segurança autorizados.

## Gates pendentes e rollback
- A PR #2057 permanece DRAFT. Não implantar nem habilitar CORTES_KWAI_CLOUD_PUBLISH_ENABLED sem revalidação de quotas, papel da conta real, verificador independente implantado, run de testes Node, readback de recibos e cutover único com fencing.
- CORTES daily/resume continuam Windows/self-hosted, com recuperação funcional completa de masters e checkpoint remotos ainda não comprovada.
- Reversão da correção em draft: Git revert específico dos commits da PR, após SHA e lease; produção não foi alterada.
- Estado final deste lease: ENCERRADO. Código READY_FOR_REVIEW, homologação de publicação PARTIAL / RECONCILE_REQUIRED.
