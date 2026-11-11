# CORTES TikTok — lote editoral canônico GitLab/Neon recuperado
STATUS: PROVEN (enfileiramento) / PARTIAL (publicação)
AREA: tiktok
DATE: 2026-11-11
OWNER: Anthares GitLab protected producer
RUN: https://gitlab.com/UniversoAnthares/anthares-clipper/-/pipelines/3056301400
JOB: https://gitlab.com/UniversoAnthares/anthares-clipper/-/jobs/17947848775
COMMIT: 15f6e7ac1703d8af341ec38e50460525a204be4e
SUPERSEDES: none

## Problema corrigido
O produtor GitLab de TikTok consultava os anexos WordPress individualmente para todos os clips antes de selecionar o lote, estendendo o processamento e consumindo minutos de runner. O código foi corrigido via GitLab MR !103, commit 15f6e7ac: seleção limitada antes das consultas e recuperação canônica de metadados com até 50 anexos por GET autenticado. O validador original de títulos e textos permanece obrigatório.

## Prova
- GitLab CI pipeline 3056298940 SUCCESS; quatro testes de identidade, 55 anexos em duas leituras, origem HTTPS exigida e quarentena por metadados ausentes passaram.
- Preflight protegido job 17947848774 SUCCESS: OIDC TikTok ACEITO, credenciais WordPress READY, 200 anexos consultados, 192 aprovados, 8 em quarentena, 29 fontes inspecionadas, 221 candidatos elegíveis antes do limite 200.
- A execução anterior do canário unitário, pertencente ao pipeline 3052117980 e baseada em código antigo, estava segurando o resource_group; foi solicitado cancelamento e confirmado CANCELED. O job atual só começou depois que o grupo foi liberado.
- Produtor job 17947848775 SUCCESS em 2026-11-11T20:42:43Z: CORTES_TIKTOK_PRODUCER_OK sources=29 eligible=221 examined=192 created=69 titles_updated=0 network_enabled=1.
- Consulta read-only ao Neon de CORTES no projeto purple-flower-35918989 confirmou 69 registros novos em public.cortes_tiktok_publications, source_id=cOhqEaY3-08, status=queued.

## Limites da prova
- 69 registros enfileirados com deduplicação e dados canônicos, nenhuma confirmação TikTok criada por esta rodada. Publicação efetiva exige consumidor autorizado e recibo.
- GitHub Actions: workflow Pinterest repair 43095740209 reportou startup_failure, sem correção executada. Outro fanout 43096306588 permaneceu queued na última consulta. Isto impede considerar aquelas execuções bem sucedidas.
- O produtor CORTES continua com 69 master MP4 armazenados, 159 segmentos elegíveis pendentes na mesma fonte; seus arquivos e checkpoint locais são preservados.
- Restam filas das demais redes, capacidade Buffer/Pinterest, reconciliação dos 15 estados incertos e migração da produção de mídia para provedor externo homologado.

## Consequência
Preservar o GitLab MR !103 implantado, o lock de resource_group, o OIDC oficial, a quarentena editorial e a deduplicação Neon. Não reconstruir fontes perdidas ou repetir enfileiramentos sem reconciliar recibos; queued não significa posted.
