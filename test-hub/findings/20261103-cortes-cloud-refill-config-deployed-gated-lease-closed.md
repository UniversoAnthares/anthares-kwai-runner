# CORTES — refill manual no Ubuntu, instalado em main com ativação bloqueada
STATUS: PARTIAL
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/231
JOB: none
COMMIT: 55807ac002d7cd2ce8e5be6017df7f3d6271db00
SUPERSEDES: 20261103-lease-queue-cortes-cloud-refill-main-gated.md
LEASE_CLOSED_UTC: 2026-11-03T21:47:14.722Z
GOVERNANCE_MANIFEST: 223433740e807a90

## Feito e prova
- PR privada Anthares Clipper #231 incorporada no main pelo SHA exato 55807ac002d7cd2ce8e5be6017df7f3d6271db00, UTC 2026-11-03T21:46:09Z.
- Arquivo .github/workflows/cortes-kwai-dispatch-refill.yml em main agora usa ubuntu-24.04, id-token: write, workflow_dispatch somente e sem gatilhos schedule/self-hosted/Windows; blob SHA 7765d4bdfaf8a3ab3424ca46a6169740b2a2de52.
- O job exige vars.CORTES_CLOUD_REFILL_ENABLED == '1'; consulta GitHub autenticada do valor devolveu 404 (variável AUSENTE), logo o workflow está inativo até nova autorização. Nenhum novo run em Clipper desde 2026-10-30. Existe run histórico queued 41126324696, sem alteração por esta atividade.
- O cliente cortes_short_dispatch.py em main (blob 04174377d2df9deed52dd692552d20fffa336922) tem URL Cloudflare allowlist, OIDC GitHub, gate adicional CORTES_CLOUD_DISPATCH_ENABLED, sem fallback ou reenvio automático diante de HTTP 4xx/erro incerto. Caminho legado permanece apenas para compatibilidade.
- Testes qa/test_cortes_hosted_refill.py em main (blob 6b89dc761a827616751a5dcf8c313a537e9dc741) contemplam URL allowlist, gate off, chamada OIDC uma vez e rejeição sem reroute. Suíte ainda aguarda execução em runner cloud autorizado.
- A PR pública #2057 (Neon/Cloudflare novo contrato) permanece DRAFT e sem deploy. O bloqueio do backend é CORTES_KWAI_CLOUD_PUBLISH_ENABLED, flag off por padrão.
- Os 68 UNCERTAIN do Kwai não foram modificados, reenviados ou marcados como confirmados.

## Estado e limites
PROVEN a instalação da nova configuração do workflow de reabastecimento no GitHub, sem dependência Windows em seu caminho e sem jobs novos.
UNVERIFIED a execução útil em Ubuntu e a publicação por conta Kwai.
PARTIAL o item de migração dos três workflows: daily e resume continuam self-hosted Windows e dependem de checkpoints e masters externos íntegros; refill está configurado para Ubuntu com acionamento bloqueado.
RECONCILE_REQUIRED para os 68 registros Kwai; WAITING_EXTERNAL para Vercel 402, respeitando custo adicional zero.

## Recuperação e próxima ação
Se for necessário voltar ao código anterior, criar PR que reverta estritamente o merge 55807ac002d7cd2ce8e5be6017df7f3d6271db00, após lease e SHA atualizados. Não iniciar PC runner para rollback. Para ativar refill externo é obrigatório provar 68 recibos de rede/estado, OIDC do workflow, Cloudflare+Neon deployed com credenciais e isolamento, quotas, checkpoint e teste real permitido em job de produção autorizado; somente então considerar a variável CORTES_CLOUD_REFILL_ENABLED.
Lease ENCERRADA. Nenhum serviço, conta ou segredo alterado por este registro.
