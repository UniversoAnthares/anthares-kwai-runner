# Kwai — cadência proporcional até 23h: evidência de produção
STATUS: PROVEN_PACING
AREA: kwai / neon-cortes-queue / anthares-publisher
DATE: 2026-11-12
GOVERNANCE_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

Regra: após primeira publicação confirmada, N cortes elegíveis são distribuídos em N+1 intervalos iguais até 23h America/Campo_Grande, com uma última janela de segurança antes de 23h. Primeiro post do dia: DUE imediato. Alteração de fila ou nova publicação comprovada recalcula a cadência. Cap 100/dia/conta. A partir de 23h: BLOCKED. Horário de publicação vem do vídeo público, com fallback publication_started_at; updated_at não controla horários.

Código: PR #2437 merged c6f2baf549708b19e3dd96828fbe4416bf3c3a80, ambas rotas kwai-physical-stats e kwai-lease usam kwaiDeadlinePacing. Testes: 11 matemáticos, quatro testes de integração; PR #2438 merged 50bf08e6cec8c7c7160ecbedbf55b000dbd97274, Actions run 43283812906 completed/success.

Neon QA cortesqueue deployment 4: completed, GET health 200 ok=true database_ok=true. Neon produção deployment 70: completed. Consulta RSA autenticada à produção comprovou pacing_version kwai-public-post-proportional-v2 em ambas as contas.

Snapshot ~14h46 -04, 12/11:
- lucasrosalem: confirmed_today 5, used 6, elegíveis 46, último horário público 18:24:43.530Z, next_due 18:35:41.327Z, intervalo 657.797s.
- universoanthares: confirmed_today 5, used 7, elegíveis 64, último horário público 14:29:00Z, next_due 14:40:33.230Z, intervalo 693.231s.
Valores são dinâmicos.

Daemon Windows: hotfix local SHA256 919F5EE3EACD1BFDACD4BAD81E8F29AA8B84923DC88935CD937B978F5258E7E6; reiniciado via scheduled task. Testes independentes de cálculo local compararam com ambos planos assinados de produção e rejeitaram versão anterior e divergência de horário. Preservar alterações locais diante de divergência com daemon legado no GitHub. A garantia autoritativa de pacing está na aprovação Neon de cada lease. ACK pendente e bloqueios de publicação são assuntos independentes.
