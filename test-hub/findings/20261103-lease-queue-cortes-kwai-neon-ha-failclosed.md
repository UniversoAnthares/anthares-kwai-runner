# Lease — CORTES/Kwai fila Neon HA sem liberação de publicador
STATUS: RUNNING
AREA: queue
DATE: 2026-11-03
RUN: none
JOB: none
COMMIT: 63c5e5c934e18cec456f69ef02f136bf6d7ff816
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / CORTES
LEASE_START_UTC: 2026-11-03T21:21:21.840Z
LEASE_EXPIRES_UTC: 2026-11-03T21:46:21.840Z
GOVERNANCE_MANIFEST: 223433740e807a90
SCOPE: proposta de contrato Kwai no Neon Functions/Cloudflare, operação fail-closed, e read-only reconciliation dos 68 UNCERTAIN. Sem deploy no ambiente ativo até validação de identidade, quota e fonte; workflow de migração hosted apenas QA sem publicação.

## BASELINE_PROVEN
- Dois Workers Cloudflare/Neon existentes: HTTP 200 health e HTTP 401 em POST anônimo. Vercel CORTES principal HTTP 402; nenhum retry/upgrades.
- Neon primary possui 68 UNCERTAIN Kwai em 3 fontes; zero exact_media_confirmed e zero overlap_confirmed; sem remote_id ou confirmation_evidence para os 68. Zero leases ativos.
- 456 registros Kwai confirmed; snapshot ledger Neon duas cópias com SHA256 verificado; mídia real do Google Drive restaurada com hash válido.
- Kwai cloud publisher do repositório público é independente da fila WordPress de @lucasrosalem; nunca confundir identidades.
- Main hub 63c5e5c934e18cec456f69ef02f136bf6d7ff816; main Clipper 8c31afffe137a9ed1d9860d10e8c8d380b3a86ec; CLIPPER_PRODUCERS inclui cortes-neon-short-dispatch.yml.

## FAILED_AVOIDED
- Não declarar UNCERTAIN confirmado por semelhança; não publicar, reenviar, alugar publicador ou alterar status na produção.
- Não habilitar CI/workflows desativados por quota, mudar credencial ou criar produto pago.
- Não utilizar PC como runner, storage ou staging. Sem deploy automático de código novo sem gate.

## SUCCESS_SIGNAL
- PR isolada com API de consulta Kwai OIDC autenticada, contrato de processamento Kwai protegido por flag default-off e id/owner/lease_generation; Cloudflare ingressos somente encaminham ações pré-registradas.
- Nova documentação/testes estáticos validam caminho de falha segura; lista das pendências de cutover explícita.
- Controle permanece sem ativar, sem upload nem mudança nos 68 UNCERTAIN.

## FAILURE_SIGNAL
- SHA divergente, lease mais antigo ativo, tentativa não autenticada aceita, impacto em outro destino, execução de mídia, custo adicional, CI novo sem aprovação/controle.

## TEST_VALIDITY
Este lease permite apenas codificação em branch e PR. Não autoriza promoção de primário, deploy da função, reativação de workflow, nem publicações de teste. Encerrar por finding append-only de resultado e próxima decisão.
