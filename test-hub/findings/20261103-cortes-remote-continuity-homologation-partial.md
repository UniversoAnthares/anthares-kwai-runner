# CORTES — homologação de continuidade externa, sem publicação
STATUS: PARTIAL
AREA: architecture
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41116819377
JOB: 124273089258
COMMIT: e5d105d24565b013ca1624cbcd5631dbb9dae403
SUPERSEDES: 20261103-lease-architecture-cortes-remote-homologation.md
OBSERVED_UTC: 2026-11-03T21:04:02.456Z
GOVERNANCE_MANIFEST: 223433740e807a90
PRODUCTION_CUTOVER: NOT_AUTHORIZED
NO_ADDITIONAL_COST: true

## Objetivo
Homologar acesso remoto a fonte, fila, controle de concorrência, integridade de ledger, recuperação de mídia e segurança sem usar PC como executor nem publicar conteúdo apenas para testar.

## Evidência PROVEN nesta rodada
1. GitHub-hosted Ubuntu: run 41116819377, log runtime CORTES_HOSTED_CANONICAL_SOURCE=PASS e CORTES_HOSTED_READONLY_GATE=PASS; FFmpeg, compilação e fonte privada compatíveis. Prova exclusivamente camada de preflight.
2. Neon existente: tabela cortes_publications com id/dedupe_key/lease_owner/lease_generation/lease_until/publication_started_at/remote_id. Consultas SELECT mostraram ausência de leases ativos e existência de registros UNCERTAIN a reconciliar, sem transmitir IDs privados ao Test Hub.
3. Neon: dois snapshots do ledger, de 2026-10-30 e 2026-10-31, verificados por comparação SQL de SHA-256 calculado dos bytes persistidos; ambos com tamanho e digest coerentes. Prova de integridade dos bytes, não de restauração transacional de produção.
4. Cloudflare Workers já existentes anthares-cortes-neon-edge-ha e anthares-cortes-queue-ha: GET ?action=health retornou HTTP 200 com ok=true e backend neon-functions-cortes. Teste negativo POST action=enqueue com JSON vazio e sem credencial retornou HTTP 401 em ambos. Nenhuma fila alterada.
5. Google Drive externo já existente: recuperada uma mídia MP4 real (4.614.015 bytes) em ambiente isolado fora do PC, SHA-256 idêntico ao manifesto original e ffprobe confirmou H.264/AAC, duração 79,6s, 640x360. Amostra prova leitura íntegra da mídia individual; nenhum arquivo ou ID privado divulgado neste repositório.
6. Suspensão dos dois CRON Windows de CORTES continua PROVEN no commit Clipper 8c31afffe137a9ed1d9860d10e8c8d380b3a86ec, sem alterações nos três workflows self-hosted; sem inicialização local.

## Bloqueios objetivos
A. Vercel anthares-remote-primary: GET health do endpoint CORTES em 2026-11-03 retornou HTTP 402. Deploy na conta aparece READY, mas acesso funcional não passou. Nenhum retry cobrando, upgrade ou mudança de plano autorizado.
B. Cloudflare é ingresso de contingência parcial: ACTIONS do Worker incluem enqueue e buffer, porém não há contrato de lease/start/confirm do publicador Kwai completo naquela rota. Dois Workers compartilham dependência do mesmo Neon. Health 200 não prova entrega final à rede.
C. Neon tem publicações UNCERTAIN com publication_started_at e sem remote_id/evidência positiva para a conta Kwai; exige verificação pública individual antes de qualquer reenfileiramento. Nenhuma reconciliação mutante foi tentada.
D. Três workflows de produção de Clipper ainda exigem [self-hosted, Windows] e usam caminhos de mídia/ledger do PC. O preflight Ubuntu não inclui recuperação de todos os media, origem e estado do lote ou identidade de publicador.
E. Google Drive contém ao menos uma mídia recuperável, mas a cobertura integral do acervo, writer único, retenção, recibos, RPO/RTO e restauração operacional dos checkpoints continuam UNVERIFIED.

## Critério terminal
Continuar com PC desligado somente após validar executor remoto para o trabalho real, origem íntegra e completa, credencial/scopes corretos, ledger persistente com idempotência e fencing, reconciliar UNCERTAIN com evidências da plataforma, provar restauração de checkpoint e confirmar publicação legítima decorrente de demanda real (sem mídia de teste), quota zero e rollback. Cutover bloqueado enquanto qualquer critério permanecer aberto.

## Consequência
Homologação read-only concluída com resultado PARCIAL; bloqueio da transferência de produção permanece. Preservar filas, arquivos, sessões, recibos e publicadores. Registrar as pendências sob o núcleo CORTES/REMOTE, sem criar novo item dos 21 AOI. Lease encerrada com este finding; futura mudança requer nova lease.
