# Lease CORTES: publicadores diretos / sem Buffer
AREA: queue
STATUS: RUNNING
START_UTC: 2026-11-12T03:06:08.315Z
EXPIRES_UTC: 2026-11-12T03:35:08.315Z

Solicitação expressa: eliminar Buffer dos novos envios, priorizar fonte atual cOhqEaY3-08 nos publicadores diretos (Instagram Graph, LinkedIn pessoal e Pinterest via browser autorizado) sem reordenar ou perder registros históricos. Este lease serializa exclusivamente os patches da fila e workflows de distribuição social. TikTok Neon, geração de cortes e Kwai mantidos intocados; preserve status uncertain e fences. Evitar tentativas antigas do Buffer e diagnósticos repetidos. Prova de conclusão: merge protegido, deploy da função Neon, execução de publicadores diretos com recibos oficiais. Se outro lease queue anterior ativo, ceder. Fecha-se em finding append-only com provas.
