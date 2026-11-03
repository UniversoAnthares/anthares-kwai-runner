# CORTES — refill Cloud Ubuntu instalado, bloqueado e lease encerrada
STATUS: PARTIAL
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/231
JOB: none
COMMIT: 55807ac002d7cd2ce8e5be6017df7f3d6271db00
SUPERSEDES: 20261103-lease-queue-cortes-cloud-refill-main-gated.md
LEASE_CLOSED_UTC: 2026-11-03T22:23:17.729Z
GOVERNANCE_MANIFEST: 223433740e807a90

## Aceite observado
- A PR 231 do anthares-clipper foi incorporada ao main, commit 55807ac002d7cd2ce8e5be6017df7f3d6271db00, em 2026-11-03T21:46:09Z.
- Workflow .github/workflows/cortes-kwai-dispatch-refill.yml do main confirmado: runs-on ubuntu-24.04, id-token: write, workflow_dispatch presente, schedule ausente, nenhuma referência self-hosted Windows. SHA 7765d4bdfaf8a3ab3424ca46a6169740b2a2de52.
- Script cortes_short_dispatch.py do main: rota Cloudflare/Neon allowlisted com OIDC, sem fallback automático; URL Vercel legada explícita apenas para compatibilidade, exige token já existente e NÃO é chamada pelo workflow novo. SHA 04174377d2df9deed52dd692552d20fffa336922.
- Teste qa/test_cortes_hosted_refill.py incluído no main (ainda sem prova de execução no runner hospedado); SHA 6b89dc761a827616751a5dcf8c313a537e9dc741.
- Consulta gh api actions/variables/CORTES_CLOUD_REFILL_ENABLED: 404 (variável ausente); logo o novo workflow só executará depois de autorização e ativação explícita, ainda não concedidas. Nenhum run novo encontrado no Clipper após a incorporação; última listagem permanece com execuções antigas de 2026-10-30, incluindo run 41126324696 queued sem jobs.
- Neon Kwai mantém 456 confirmed / 68 uncertain, nenhuma modificação por esta migração.

## Bloqueios / segurança
- Migração de código para hosted = DEPLOYED (workflow desativado por gate); publicação = UNVERIFIED e cutover = WAITING_EXTERNAL / RECONCILE_REQUIRED.
- API Cloudflare/Neon Kwai está somente proposta na PR pública draft #2057; não foi implantada/ativada.
- Os dois workflows de geração daily/resume continuam dependentes de runner local e de arquivos/checkpoints. Nenhum master ou dado pessoal foi movido/removido.
- Evitar habilitar flag, acionar manualmente job, publicar para teste, reencaminhar UNCERTAIN ou usar o PC.
- Para reverter a implantação de código, usar nova PR revertendo o merge 55807ac, após conferência do head; sem tocar os ledgers.

## Registro
Esta evidência encerra a lease da PR #2059 anteriormente incorporada no Test Hub. Não reabrir a lease vencida; novas operações exigem coordenação e lease separadas.
