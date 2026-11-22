# Anthares Studio — PR #403, Gantt e ACF (22/11/2026)

STATUS: PROVEN_IN_CODE_AND_HOSTINGER; AUTHENTICATED_VISUAL_QA_PENDING.
LEASE: test-hub/findings/lease-studio-gantt-sync-20261122.md, início 10:14 local, encerramento 10:26 local. STATUS: CLOSED_SUCCESS.
OWNER: ChatGPT / STUDIO_GANTT_SYNC_20261122.

## Execução
- Código: UniversoAnthares/anthares-wordpress PR #403, merge squash `374510df80cc4706ee0de05c9138ed99e6871181`.
- Corrigido Gantt de entrada sem saída no recorte de capítulos: limite em coordenadas da obra `offset+length+1`. Pares entre capítulos e saídas órfãs mantidos.
- Barras do Gantt: seleção por mouse/teclado, informações sobre personagem, IDs/posições e navegação ao Quill; foco e indicação visuais.
- Administração ACF: edição de valor pelo mesmo handler transacional da edição autoral, atualizando CPT e Delta. Campos de vínculo e posição somente leitura e verificados no servidor; recusas restauram os campos e exibem aviso.
- Código PHP/JS/CSS publicado na Hostinger após comparação dos hashes de origem e destino, backups privados, lint PHP 8.3, escrita atômica e verificação dos hashes finais.

## Hashes Git blob conferidos em produção
- `includes/domain/class-anst-manuscript-markers.php`: `b41c974169e84276fa601d8a558be45d4fa51cbd`
- `assets/studio-manuscript-markers.js`: `b85ce014ca51c712813f5f05eae22ea3af537c7b`
- `assets/studio-manuscript-markers.css`: `1d0e1513020e17312500f3d64875f0d801da74fc`
- Backup: `/home/u566597497/domains/anthares.us/studio-private-backups/20261122-gantt-acf-pr403/`
- Legado `/estudio/` arquivo principal preservado: blob `e4a9812ac21b5c977b93e53fe65131b43e23ba85`.

## Testes
- WordPress real: `qa_manuscript_markers_transaction.php`: TOTAL_PASS=54, ROLLBACK=EXECUTED; inclui 4 novos testes ACF (edição normal, Delta sincronizado, campo imutável e valor inválido).
- Regressão narrativa: `qa_narrative_timeline_transaction.php`: TOTAL_PASS=27, ROLLBACK=EXECUTED.
- Testes estáticos dos marcadores: 10/10 em Python unittest.
- QA do repositório: `QA_MANIFEST_PREFLIGHT=PASS auditable=761 assigned=761 exactly_once=yes`.
- PHP 8.3 lint: dois arquivos PHP atualizados/testados, sem erros.
- Parser V8: `studio-manuscript-markers.js` sem erro. Quatro cenários funcionais do Gantt exercitados em memória: barra aberta intercapítulos, entrada/saída intercapítulos, entrada interna em aberto, saída órfã vermelha sem barra.
- HTTP 200 em `/studio/` e `/estudio/`; JS e CSS servidos com hashes acima.
- Staging remoto próprio removido após conferência de HEAD; backups de rollback preservados.

## Pendente de homologação
- Teste visual end-to-end autenticado com mouse, teclado e mobile continua no item 21.
- Item 10 (Curva da Desgraça): editor pedagógico anterior com dois marcadores livres e migração de registros antigos ainda carece de decisão/integração; curva vinculada ao manuscrito está implementada.
- Gráfico de Estilo segue pendente de métricas editoriais.
