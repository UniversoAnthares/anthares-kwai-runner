# Lease: CORTES todos os curtos em cinco redes
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-21
RUN: none
JOB: none
COMMIT: 2b32df2151a67fe7a43b39a73671a00e8136f4e6
SUPERSEDES: none
LEASE_AREA: cortes-short-all-five-dispatch-policy
LEASE_OWNER: chatgpt-current-conversation
LEASE_MAX_EXPIRY_UTC: 2026-10-21T16:00:00Z

## Objetivo
Cada master curto de 30-90 s persistido no WordPress gera destinos independentes: Kwai, TikTok, Instagram, Pinterest, LinkedIn, sem omissão por quota artificial. Enfileirar todos; publicar respeitando rate limits reais e controles de conta; não equiparar enfileiramento à publicação.

## BASELINE_PROVEN
Clipper GitHub main bc80cba33be312ba1e15af84ad23402968762274; GitLab main 64f51fab9866cb9123acbc0931ed3ea257f4fc5b (histórico divergente), arquivo cortes_short_dispatch.py sha dd730ebfa229f94598393917384eb3fe70254b29. Runner GitHub main 2b32df2151a67fe7a43b39a73671a00e8136f4e6, Vercel prod branch hotfix TikTok diverge. Não fazer mirroring ou deploy destrutivo.

## FAILED_AVOIDED
Não forçar mais de 25 Pins/24h pelo Buffer, não simular endpoints para burlar cotas, não confirmar publicação a partir de agendamento, não fazer retry de jobs UNCERTAIN, não alterar publicação Kwai/TikTok existente. Pinterest bulk native/Instagram import até 150/dia dependem de pré-requisitos reais.

## SUCCESS_SIGNAL
Política codificada, fanout independente dedupe por segment+destino, testes sem rede, CI; todos os masters 30-90s originam fila; sem truncamento ao atingir quota de canal.

## FAILURE_SIGNAL
Sem credenciais de canal, falha OAuth, colisão de identidade, overlap dedupe incorreto, credenciais faltando -> preservar backlog, não publicar e registrar pendências.

## TEST_VALIDITY
Testes sintéticos não comprovam posts reais. Prova final requer canal Buffer e API key, cron instalado, publicação real com URL e evidência de ledger.
