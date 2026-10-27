# QA P0 — evidências operacionais e gates de recuperação (2026-10-27)

Origem da evidência: leitura via Anthares Remote/ARA no host autorizado DESKTOP-FTDK0HP. As observações de estado são pontuais; não constituem prova de publicação remota.

## #528 — PINTEREST_DRAFT_CAPACITY_EXHAUSTED
- D:/AntharsWork/cortes-pinterest-local/pinterest-watchdog-health.json: publisher=BLOCKED_DRAFT_CAPACITY; qa=PINTEREST_DRAFT_CAPACITY_EXHAUSTED; chrome=HEADLESS_PROFILE_UP; confirmed=17.
- pinterest-browser-events.log: registros repetidos PINTEREST_DRAFT_CAPACITY_PAUSED count=50 até 2026-10-27T11:43:02Z.
- Uma nova tentativa de upload violaria a proteção de capacidade e poderia introduzir duplicatas/rascunhos órfãos. É obrigatório conciliar os 50 rascunhos individualmente com URL pública, origem, job e estado do ledger, antes de liberar novo envio. Não excluir rascunhos incertos automaticamente.

## #492 — PIN_PUBLISH_BUTTON_NOT_READY
- Perfil AntharesPinterest existente está ativo, CDP 9226.
- Incidente anterior: mídia carregada, único botão Publicar disabled=true.
- O bloqueio de 50 rascunhos impede validação segura de uma nova publicação. Investigar o formulário existente sem executar POST, identificar campos/etapas pendentes e registrar evidência de UI; só comprovar resolução com segunda URL pública e ledger confirmado.

## #460 — mídia HTTP 404
- Registro original contém hash da URL e ID do job; nenhuma URL sensível foi reproduzida.
- Localizar origem no WordPress por identificador/fingerprint, validar HEAD/GET HTTP 200 e conteúdo antes de eventual reprocessamento.
- Preservar quarantine por vídeo e ledger STARTED/UNCERTAIN; jamais liberar retry apenas porque o arquivo passou a responder HTTP 200.

## QA em eventos e recuperação
- O controlador existente responde a issues [opened, reopened, labeled], verifica backlog a cada cinco minutos e prioriza #460/#492/#528.
- Execuções recentes dos três casos produziram DIAGNOSTIC_ONLY_NO_APPROVED_REPAIR e CODEBERG_RESULT_UNAVAILABLE; são confirmações de diagnóstico, não de conserto.
- PR #1506 integrado (commit 5c0304e15c9d042aa3e3abb4e1d7331de06ede50): três regressões Python e dois YAMLs validados no Windows. PR #1513 integrado (commit f9ce21b7db3f2463d530b4906ad873b0eda09c8a): quatro testes Node aprovados, YAML validado e auditoria real read-only confirmada no executor P0 #528 (Actions run 40501533187). A falta de Codeberg corrente mantém a ação de QA com resultado geral de falha, mesmo quando seu subdiagnóstico local é executado.

## Condições de encerramento
- #460: FECHADO em 2026-10-27 como mídia expirada e descartada, alternativa expressamente prevista na ocorrência. Neon confirmou status=failed, source_media_expired_24h, HTTP 404, confirmed_on_network=false, sem publicação iniciada, sem remote_id nem lease ativo.
- #492: segunda publicação pública distinta comprovada por URL + ledger, sem duplicata.
- #528: capacidade abaixo do limite, rascunhos inventariados/reconciliados e retomada segura confirmada.

## Reconciliação Neon e auditoria do navegador — fatos de produção em 2026-10-27
- Banco de produção `purple-flower-35918989`, tabela `public.cortes_publications`, destino `pinterest:lucasyahn`: 17 `confirmed` (16 `buffer_pinterest_sent_verified`, 1 `pinterest_browser_verified_pin`); 208 `failed` (203 `pinterest_expired_after_next_day`, 5 `source_media_expired_24h`); 8 `uncertain` (7 sem evidência de confirmação e 1 `buffer_scheduled`); zero registros `queued` ou `leased` na amostra.
- O job do issue #460 `cortes-fanout-pinterest-c1d15494f7502c68bbb6febecca6c017` possui registro definitivo `source_media_expired_24h`, `http_status=404`, `confirmed_on_network=false`, expirado em 2026-10-23T12:11:35Z; o issue foi encerrado `not_planned` por descarte previsto.
- O Pin `819514463494243592` é a única publicação diretamente comprovada pelo navegador. As 16 confirmações posteriores via Buffer não comprovam correção do executor de UI. Issue #492 permanece aberto.
- A auditoria do Chrome (CDP 9226, read-only) detectou 50 rascunhos: 40 com título editorial, 10 sem título editorial, 33 fontes de miniatura e 8 grupos de exibição repetida. SHA-256: `d2f292a5365ca48222265213a9cabfda6c438bf765003780a6483ffc113a6028`. Esse resumo foi escrito automaticamente no issue #528 pelo Actions run 40501533187. Rascunhos são potencialmente diferentes mesmo quando têm a mesma miniatura; nenhum foi excluído nem reenviado.
- Próxima ação segura: confrontar cada rascunho com a identidade de mídia, job e resultado remoto; preservar os oito estados `uncertain`; liberar capacidade só após provas individuais. A publicação de um segundo Pin pelo executor local necessita capacidade disponível e validação do ledger.
