# Distribuidor multicanal — destination_key em produção
STATUS: PROVEN
AREA: queue
DATE: 2026-10-06
RUN: none
JOB: AI Commander deploy-distributor-v040 / verify-atd-destination-column
COMMIT: 9c9f8b12302e58082e5614f3966d8f325080db26
SUPERSEDES: none

## Objetivo
Remover a suposição de provider/conta única no Distribuidor WordPress e preparar cinco destinos: tiktok:primary, kwai:primary, kwai:secondary, instagram:primary, threads:primary e x:primary.

## Resultado
Plugin Anthares TikTok Distributor atualizado para 0.4.0 e implantado. Delivery ganhou platform, account_id, destination_key, lease_generation, publication_started_at e confirmation_evidence. API ganhou publisher/started e publisher/renew; finish exige lease_generation atual e, para published, started + remote_id + confirmation_evidence. Admin exibe estados separados por destination_key.

## Evidência decisiva
Todos os PHP do plugin passaram php -l em clone fresco no host. Site respondeu HTTP/2 200 após deploy. wp --skip-themes carregou ATD_VERSION=0.4.0. Consulta via $wpdb em produção confirmou a coluna destination_key.

## Consequência
Novos adaptadores DEVEM usar platform+account_id. kwai:secondary nunca reutiliza estado de kwai:primary. HTTP de publish sozinho não fecha delivery; confirmation_evidence é obrigatório.
