# CORTES/Kwai — regressão de failover que poderia repetir escritas corrigida em draft
STATUS: PARTIAL
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2057
JOB: no CI run / isolated in-process tests
COMMIT: 6edb1e00c54a378da79e670746becd4fb389bf2f
SUPERSEDES: none
OBSERVED_UTC: 2026-11-03T22:27:46.510Z
GOVERNANCE_MANIFEST: 223433740e807a90

## Problema de segurança
O Worker secundário Cloudflare de CORTES podia encaminhar uma mutação ao segundo endpoint Neon depois de HTTP 5xx ou erro de transporte. Esses sintomas podem ocorrer após o primeiro endpoint ter gravado no banco. Repetir lease/start/confirm ou quota nessas condições é incompatível com reconciliação idempotente e o contrato de resultado UNCERTAIN.

## Correção STAGED em PR #2057
- No arquivo cloudflare-cortes-queue-ha/src/index.mjs, o HTTP 5xx de um POST passa a ser devolvido ao chamador sem retry. Em caso de timeout/erro após possível gravação, retorna 503 mutation_result_uncertain_no_replay sem consultar o segundo backend.
- O failover continua permitido para health GET, que é operação somente leitura.
- Testes de regressão adicionados a tests/cortes_kwai_cloud_contract.test.mjs para a resposta 5xx e exceção de transporte, sem acionar serviço externo.

## Prova local isolada, sem execução GitHub Actions
O módulo do Worker em branch foi carregado em avaliação JS com Responses/Headers e fetch simulados, sem rede, sem mídia e sem secrets. Quatro testes independentes passaram:
1. POST kwai-start com resposta upstream 503 => 503 devolvido, fetch exatamente 1 vez.
2. POST kwai-confirm com timeout depois de tentativa de envio => 503 mutation_result_uncertain_no_replay, fetch exatamente 1 vez.
3. GET health com falha 503 no primário e 200 no secundário => 200, fetch 2 vezes.
4. POST kwai-enqueue sem Authorization => 401, fetch 0 vezes.
Também houve validação de sintaxe JavaScript em branch. Os testes de CI permanecem preparados, sem execução hosted neste finding.

## Reconciliação externa
Tentativa única de verificação pública de título recente na conta Kwai via pesquisa web não apresentou link verificável; leitura direta de perfil na ferramenta pública não ficou acessível. Ausência de resultado indexado não é prova de ausência de publicação. Os 68 registros Kwai UNCERTAIN permanecem íntegros, sem alteração. Confirmar apenas por URL Kwai oficial e readback de conta e vídeo pelo validador já existente.

## Status e limites
- Correção de replay: STAGED/READY_FOR_REVIEW em PR #2057, sem deploy Neon/Cloudflare nem ativação de publicador.
- Proteção em produção: permanece na versão implantada anterior; avaliar antes de incluir novas ações de publicação.
- Refill: código Ubuntu já incorporado no Clipper no commit 55807ac, gate CORTES_CLOUD_REFILL_ENABLED ausente, sem execução.
- Daily/resume: dependências Windows/checkpoints ainda pendentes.
- Nenhum custo adicional, vídeo publicado, job disparado ou alteração de ledger nesta investigação.
