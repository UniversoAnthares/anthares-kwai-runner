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
- O PR #1506 adiciona gates de diagnóstico individualizados e testes de regressão. Requer CI validado e promoção do PR, seguida de nova verificação em produção.

## Condições de encerramento
- #460: origem reparada e GET autenticado/público conforme contrato; quarentena/ledger reconciliados.
- #492: segunda publicação pública distinta comprovada por URL + ledger, sem duplicata.
- #528: capacidade abaixo do limite, rascunhos inventariados/reconciliados e retomada segura confirmada.
