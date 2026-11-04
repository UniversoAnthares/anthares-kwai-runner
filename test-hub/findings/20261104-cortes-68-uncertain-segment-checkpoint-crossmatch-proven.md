# CORTES — 68 UNCERTAIN correspondem integralmente ao checkpoint remoto
STATUS: PROVEN
AREA: queue
DATE: 2026-11-04
RUN: none
JOB: Neon SQL SELECT, sem efeitos
COMMIT: cbf4a587ba3408d12905681107801f461459e553
SUPERSEDES: none
OBSERVED_UTC: 2026-11-04T02:56:21.177Z
GOVERNANCE_MANIFEST: 223433740e807a90
ITEMS: [AOI-21]

## Hipótese
Os 68 registros de publicações Kwai incertas poderiam ter perdido sua identidade temporal ou seus segmentos no checkpoint após dependência do PC. Comparar por origem, segment_id e intervalos, em leitura somente do Neon.

## Dados e prova
- Neon table cortes_publications para target_key kwai:lucasrosalem: 68 UNCERTAIN, todos com unique id/dedupe_key/source interval, sem remoto/recibo.
- Último snapshot completo de cortes_media_ledger_snapshots: revisão 15399, SHA256 válido, 2.932.006 bytes, cinco fontes (2026-10-31T04:42:38.710Z).
- Todos os 68 registros têm uma fonte correspondente no campo sources do snapshot (51, 16, 1), por source_id + ':g1'.
- Junção JSONB segment_id + fonte do snapshot contra tabela retornou 68 registros correspondentes, 68 identidades distintas, zero segmentos ausentes.
- Em 68/68 correspondências, diferenças absolutas de start_seconds/source_start e end_seconds/source_end <= 1 segundo; diferenças >1s: zero.
- Identidade do mesmo segmento foi comprovada sem ler/transmitir dados secretos, tokens de callback ou URLs privadas.
- As 68 mídias WordPress relacionadas foram comprovadas em outro finding por HEAD 200 / video/mp4; não são recibos do Kwai.

## Limite de validade
PROVEN integridade referencial da seleção de segmentos na fonte/ledger e disponível no banco; não significa que qualquer clipe foi publicado na plataforma Kwai. Status dos 68 segue RECONCILE_REQUIRED. Proibir retry ou duplicação enquanto faltar readback autenticado da conta; 3 confirmados antigos com remote_id ausente precisam de verificação adicional separada.

## Próxima decisão
Concluir verificador remoto independente com atestação, validar contrato da PR draft #2057, obter recibos reais por conta/segmento e somente depois revisar os estados. Migração dos workflows daily/resume depende de recuperação real de media masters e checkpoint no executor externo e quota R$0 comprovada. Nenhuma mutação de produção, CI, vídeos, agendamentos ou cobrança realizada neste trabalho.
