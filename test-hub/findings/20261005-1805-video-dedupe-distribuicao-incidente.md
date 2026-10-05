# Incidente de repetição de cortes e baixa distribuição TikTok
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: 693d955bb57d675568e33053ce96c45a5acb4ea9, 88c143f530e562ae6d1f3f4a388f5fef2f70d464
SUPERSEDES: none

## Objetivo
Registrar o incidente observado em produção e endurecer a seleção de cortes contra reaproveitamento da mesma timeline.

## Resultado
Foi identificado um defeito concreto no gerador Kwai legado: o início era calculado por módulo da duração da fonte, portanto a sequência inevitavelmente voltava a trechos anteriores. O ledger do publicador deduplicava queue_id/SHA-256 do arquivo, o que não detecta dois arquivos diferentes contendo o mesmo trecho da fonte. Foi adicionado um histórico persistente por fonte+intervalo e a geração agora recusa qualquer intervalo que intercepte timeline já reservada; ao esgotar uma fonte, falha fechado em SOURCE_EXHAUSTED_NO_UNUSED_TIMELINE. No pipeline autoral TikTok, a tolerância anterior aceitava sobreposição inferior a 55%; a análise v4 agora rejeita qualquer sobreposição temporal positiva na mesma fonte.

O usuário também apresentou evidência visual de que dois posts manuais no TikTok obtiveram visualizações, enquanto vários posts automáticos próximos ficaram em 0-3 views. A causa algorítmica ainda não está comprovada. A cadência automatizada configurada no pipeline chega a meta de 100/dia e intervalos de 61-300 s, portanto frequência/rajada deve ser tratada como hipótese de risco e testada separadamente antes de novas publicações em volume.

## Evidência decisiva
kwai_daily_daemon.py antigo: start=((n-1)*STEP_SECONDS)%max(1,SOURCE_SECONDS-CLIP_SECONDS-1), que matematicamente reutiliza posições quando n cresce. publisher_common.py compara queue_id e file_hash, sem identidade temporal da fonte. youtube_tiktok_pipeline.py usava _overlap_ratio >= 0.55, permitindo sobreposição parcial entre cortes.

## Consequência
Nenhum gerador futuro deve selecionar um segundo corte que compartilhe sequer 1 segundo com intervalo já reservado/publicado da mesma fonte. Dedupe por SHA-256 permanece como segunda barreira, nunca como única. Estado de intervalos deve sobreviver a reinício e mudança de dia; contadores diários jamais podem zerar o histórico de timeline. Ao esgotar a timeline inédita, selecionar outra fonte ou parar; nunca aplicar módulo/wrap-around. Para TikTok, não atribuir a baixa distribuição a uma causa específica sem teste controlado; evitar novos lotes de alta frequência até comparar publicação manual e automatizada com mídia/cadência equivalentes.
