# Item 5 — leitura autenticada do Buffer: 13 registros antigos sem ID remoto
STATUS: PARTIAL / LEASE CLOSED
DATE_UTC: 2026-11-11
AREA: cortes-item5-buffer-history-readback
OWNER: chatgpt-item5-legacy-buffer-readback
SUPERSEDES: test-hub/findings/lease-cortes-item5-legacy-buffer-readback-20261111.md
CLOSED_LEASE: true
BASE_HEAD: bd098f587ea3644b03608e5ab21411ebb2eb080e

## Comprovante operacional
- PR #2350 incorporada em dddcd24a3d21a8440a81ec5072339aa28e92d672, apenas modalidade de consulta autenticada sem publicação.
- GitHub Actions https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43023164219 = sucesso; etapa "Publish one LinkedIn cut and reconcile scheduled publications" SKIPPED e execução só de leitura.
- Buffer account/organization/channel validado. Registros incertos sem remote_id correspondem a 4 Instagram, 2 LinkedIn principal, 7 Pinterest. URL de mídia de cada registro foi representada apenas por impressão digital de 24 dígitos.
- Censo histórico completo conforme paginação por createdAt: Instagram 200 posts, LinkedIn 40, Pinterest 37, total 277.
- Matches por assets.source contra URL original de cada item: Instagram 0/4, LinkedIn 0/2, Pinterest 0/7. Zero comprovantes externos obtidos para esses 13.
- Interpretação restrita: Buffer pode reescrever/reimportar assets.source; ausência de match por URL NÃO prova que o vídeo está ausente da rede social. Continuam uncertain e bloqueados contra reenvio.
- Outros 14 Kwai têm evidência histórica previa de public_scan sem correspondência pública, não alterada nesta operação. Três Instagram Buffer IDs retornaram erro em consultas prévias; sem comprovação pública de ausência.
- 2 Pins Pinterest ainda agendados para 2026-11-11T14:24Z e 15:40Z; rotina produtiva já programada para reconciliar depois.

## Contrato
Nada foi publicado, reenviado, excluído, reclassificado sem provas, alterado por Neon SQL ou executado no PC/Android. Nenhum teste adicional foi criado ou executado.
O item 5 permanece aberto pela ausência de comprovantes de 37 registros no último censo, e não pode ser declarado DONE por sucesso do job de leitura.
