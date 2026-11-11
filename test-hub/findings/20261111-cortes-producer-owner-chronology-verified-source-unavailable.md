# CORTES — encerramento do lease de recuperação 03:30Z
STATUS: PARTIAL / PRODUCTION_OPEN
AREA: cortes-cloud-producer
OWNER: chatgpt-clipper-producer-recovery-20261111
DATE: 2026-11-11
LEASE_CLOSED: test-hub/findings/lease-cortes-cloud-producer-recovery-20261111-0330.md
BASELINE: Anthares clipper main b04dfc2ff8fc0e899c06b3ba46b275e63b292fd0; CORTES run 42951439647 blocked by YouTube bot challenge; Neon production snapshot rev 15399 / no writer CAS head.

## Código aplicado em Anthares Clipper
- PR #271, commit ab0dd8465eeb82f68df47aeab7ab7b2a1978ad48: auditoria de origem WP/source-cycle/registro e FTP remoto, Ubuntu, zero writes.
- PR #272, commit e0231b4389f1f85b3700c8a8ffb5845b48ae449d: contagens robustas e erros auditáveis sem dump de dados sensíveis.
- PR #273, commit ef0a8d40816a2a30e6152baad14ca7a86b5070e9: corrige tuple do except FTPS.
- PR #274, commit 9b66386bb2c38895962183d91f2bd1dca3eee0d0: owner-video identity/status via OAuth oficial sem download de mídia.
- PR #275, commit b7007e439ca1747445f1e1bb64685463bbbeb55c: múltiplas lives ausentes do /streams recuperadas apenas após prova de channelId, owner, privacidade, actualStartTime/EndTime e identidade da sequência pública; lotes videos.list <=50; testes adversariais em Ubuntu.
- PR #276, commit feeec25bff5ed6a9e6460d551cb161e7933c0078: estende busca FTP aos diretórios 2023/10 e 2023/11, correspondentes à live real.

## Evidências e sinais
- 42952763954: diagnóstico diário anteriormente FAILED com CORTES_UNLISTED_INVENTORY_AMBIGUOUS.
- 42954935822: CI de 8 testes sintéticos e regressões legadas: SUCCESS.
- 42955009596: diagnóstico diário real SUCCESS: CORTES_SOURCE_OWNER_CHRONOLOGY_RESTORED e CORTES_SOURCE_OWNER_CHRONOLOGY_READONLY_PASS; 28 fontes pendentes, writes=0, Windows skipped.
- 42954120535 e 42954480955: WP/FTP e owner-readback SUCCESS. Origem exata cOhqEaY3-08 está no bloqueio do WP source-cycle, stage detected, 0 clips, 0 source_file, 0 site_video_url; versão pública com owner verificado e início/fim 2023-10-14, sem bytes de mídia recuperáveis pelo WP/FTP.
- 42955369925: após expandir leitura FTP para 2023/10, a mesma fonte continua SOURCE_NOT_FOUND_IN_BOUNDED_DIRS; source_archive_filename=null, HTTP Range UNTRUSTED_OR_ABSENT, wp_writes=0, ftp_writes=0, neon_writes=0, media_downloads=0.
- Quatro Google Drive OAuth links foram verificados: busca pelo ID e busca sem filtro temporal de arquivos MIME video retornaram nenhum arquivo de vídeo; não foi encontrado master original.
- 42951016929: cookies GitHub sem linhas válidas de domínio YouTube; 42951439647: tv_embedded_hls parou em youtube_bot_challenge. Proibido repetição sem alteração causal. Nenhum original antigo reprocessado.
- Neon produção purple-flower-35918989: cortes_cloud.cortes_short_ledger_head ausente; snapshots rev 14688/15399, último há dias; PR #229 QA contém CAS, mas ainda sem role LOGIN/segredo isolado/transferência de writer. Sem cutover.

## Pendências objetivas
1. Recuperar legitimamente MP4 original da live publicada no YouTube da conta proprietária, pelo YouTube Studio (download de próprio vídeo) ou Google Takeout, OU encontrar uma cópia exata com identidade e SHA preservados em outro armazenamento já autorizado. Atual conexão OAuth da API YouTube comprova propriedade e metadados, sem fornecer URL/bytes para download oficial. Não usar IP rotation/captcha evasion ou alegar bot challenge resolvido.
2. Conectar o produtor Ubuntu a um checkpoint CAS persistente com escritor Neon de mínimo privilégio e fencing entre executores, usando staging QA existente antes de promover à produção, e armazenar masters fora do PC.
3. Provar ao menos um master real 30-90s, 720x1280, audio/video, metadados editoriais, SHA, URL persistente e inserção WordPress/Neon sem duplicar; comprovar cron diário do processamento fora de PC/Android.
4. Não habilitar Windows / rotina source_only como produtora nem publicar master sintético.

## Critério de encerramento
LEASE_CLOSED. Reparo de cronologia PRODUCED AND PROVEN. Fonte original remota NOT_AVAILABLE in checked stores. Produção diária de novos MP4 CLOUD NOT_PROVEN. Mantidos bloqueio único, fila, arquivos antigos, publicadores e cron existente. O usuário pediu conclusão plena; deixar PENDING com estes gates explícitos, sem fabricar prova.
