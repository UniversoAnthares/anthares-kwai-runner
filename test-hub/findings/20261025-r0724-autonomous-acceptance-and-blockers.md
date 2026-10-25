# Universo Anthares — Test Hub / R07.24 — execução e aceite de pacotes autônomos

- Data verificada: 2026-10-25, America/Campo_Grande.
- Executor: ChatGPT / chat de continuidade solicitado pelo titular.
- Escopo: somente `test-hub/findings/20261025-r0724-autonomous-acceptance-and-blockers.md`, branch documental dedicada.
- Base main: `05ae946b79949cb6d43e4134972c10943c9b62a1`.
- Governança: `D:\AntharsWork\governance\policy.py audit`: 218/218 projetos, 0 falhas; preflight com proprietário `chatgpt-r076-remaining-independent`, job `r076-completion-20261025-next`, versão `f6fc9ca59a96e451`.
- Preflight da própria pasta de governança recusado: documentação portátil do projeto inexistente; não executar `sync` global contra 218 repositórios por essa razão.
- Fonte oficial: https://docs.google.com/document/d/1SkjpRPJYLe9n_9SDOA4s-RibN8Pb_hm6-ukS6pbV7aQ/edit — revisão R07.24, batchUpdate com requiredRevisionId, readback confirmado.
- Relatório auxiliar: https://docs.google.com/document/d/1tm2HG1YdG9NAxs3ccVJnxAt1Dp8uAj21NdXRLJCD-VE/edit .
- Rollback: fechar PR; o checklist foi atualizado em transação Google Docs e pode ser revertido por histórico de revisões, sem alterar código produtivo.

## Aceites de escopo autônomo confirmados nesta rodada

**11 QA-02 — ACEITO para uma fila/conta.**
A automação já existente `CORTES — fila e Vercel`, ID `6ad4bdb43b34819192b0bdbc3aae5a09`, roda de hora em hora, com leitura SQL Neon `purple-flower-35918989/br-crimson-unit-b89nau08/public.cortes_tiktok_lucasrosalem4_publications`. A execução real reportada às 08h42 UTC (run `ac95af19-645c-8323-bb68-523b1926e750`) classificou queued, STARTED, UNCERTAIN, confirmed, closed_unverified, leases e IDs remotos. Emitiu alerta por aumento de itens queued >24h de 100 para 129. Nenhuma publicação ou mutação SQL causada pelo monitor. Não atesta tratamento da fila.

**16 OPS-01 — ACEITO para limite de UMA capacidade de serviço.**
`C:\ProgramData\AntharesOps\DR02\send_alert.py`, SHA256 `84A0DE87A5DB4189E48FBB9ABCFCFBD17BA73CC626684C2FF26FBB052CF26889` integra `quota_budget.py`, SHA256 `2B1918C0F768B70ADBF3B36F325869EC780CC85FE30E62225406B97E4B161E88`. Limite rígido 5 e-mails/dia UTC, reserva persistente, idempotência/fingerprint, UNCERTAIN consome limite, reset UTC. Revalidação `python -m unittest -v test_quota_budget`: seis testes PASS, exit 0. Não comprova limites de IA, Vercel, Neon etc.; não houve cobrança.

**26 MAIL-01 — ACEITO para um evento por dois meios distintos.**
Evento `ANTHARES-MAIL01-R0723-20261025-0825`. A Hostinger→Gmail: Gmail INBOX `1a17306e861d9ce8`, busca exata retornou 1. B Gmail→Hostinger: Gmail SENT `1a17306e50877ac4`, Hostinger INBOX UID `18`, data 2026-10-25T12:26:34Z, Message-ID `<CABSY5p4qtpWK595t=mr6Tv-K3f2BBB=nE19qD3X7baz_kvduOg@mail.gmail.com>`, busca exata retornou um registro. Evidência original do executor de e-mail na PR #1368 (draft), sem segredos/attachments e sem reenvios.

**31 DR-02 — ACEITO para uma família de recursos.**
Windows Scheduled Task `Anthares-DR02-Governance-Audit-12h` sob SISTEMA, 12/12h. `audit.py` SHA256 `6FDF2E3CA29125834F9A60B685AD4C0D22A1350BA35D9D413AF2434BBB7E975B`. O código verifica hashes do manifesto, expiração, quota e ACL. Histórico confirmou `ALERT` com `QUOTA_EXCEEDED:windows-c-disk-usage` e `ACCESS_DRIFT:governance-manifest-acl`. Exit code 2 é o estado ALERT definido por `run.py`, não falha de boot. Complemento da automação de riscos ChatGPT ID `6add68fbe204819184691d9cfe4a082a` ativa. PR governance #9 CI vermelho na inicialização (sem passos), não confundir com aceite hospedado. Não significa auditoria global de todas as contas.

## Avanços limitados / pendências

**06 SEC-01:** CLI Bitwarden Secrets Manager `bws.exe 2.1.0` instalado, mas `bws project list -o json` somente leitura falhou exit 1 por ausência de token de machine account no executor; não listar secret_refs nem afirmar isolamento.

**09 CORTES-ISO-04:** QA Neon tem roles LOGIN `cortes_threads_limited_r0723` e `cortes_instagram_limited_r0723`, com NOBYPASSRLS/NOCREATEDB/NOCREATEROLE. Teste de login por `role_name` via Neon retorna `missing authentication credentials: required password` para ambas. Policies da canary ainda vinculadas às roles NOLOGIN. Sem testes SQL reais ALLOW/DENY cruzados; produção sem FORCE RLS. Não dar GRANT para destravar.

**12 DB-01:** Executor A evidenciou restore lógico Neon QA 1607 + 240 linhas SHA coerentes e limpeza final sem tabelas temporárias/locks. Não substitui restauração PITR/externa nem RPO integral.

**17 CI-14:** GitLab projeto anthares-clipper pipeline `2984707689`, job `17438862167` status failed, `failure_reason=ci_quota_exceeded`, started_at=null. Não culpar código nem relançar sem quota/runner.

**19 CF-02:** PR #1346 somente correção CAS do recibo 409, sem staging/rollback real.

**Discos/produção:** preflight do CORTES diário em `qa/cortes_06am_preflight.py` exige pelo menos 2GiB livres no volume D do `runner-media`. Execução #40194127868 falhou `CORTES_DUO_6AM_DISK_LOW`; não afrouxar limite. Foram compactados reversivelmente 11 .evtx antigos, 19 temporários e caches inativos somente quando hash SHA256 se manteve idêntico; C estava com 204 MB no ponto crítico, e posterior leitura recuperou ~13,8GB por diversas operações de outros agentes. Arquivamento para F falhou antes da cópia, fonte preservada. Nenhuma mídia/publicador/credencial/aba pessoal apagada.

**22 MEDIA-01:** duas cópias reais do mesmo master por dois perfis Google Drive têm SHA256 `4ce5255d655d2017615bed36309008d8632d2e007b8fc8e361430516017eb49b`; restores e ffmpeg testados antes. Falta master genuíno NOVO capturado pelo agendamento F1, pois os arquivos de teste anteriores não provam aquisição futura.

**28 AI-04:** PR #1345 (draft) com circuit breaker e 12/12 testes GitHub Actions PASS, sem integração à produção.

**10 ISO-03:** PR #1369 (draft) corrige import por UID da PR #1338 (draft); QA hospedado ainda não aceito.

**DOC-01 / rastreabilidade:** Checklist central está na R07.24 com estados e evidências, e este Test Hub com owner, branch, SHA, data, testes, rollback e pendências. Documentos posteriores de outros executores devem ser reconciliados, não sobrescritos.

## Estados reconciliados — 34 controles

- ✅ Concluídos *no pacote autônomo definido*: 01, 02, 03, 04, 11, 16, 25, 26, 31, 34. Total 10.
- 🟡 Parciais: 05, 06, 07, 08, 09, 10, 12, 15, 18, 19, 22, 24, 27, 28, 32. Total 15.
- 🔴 Pendentes: 13, 14, 17, 20, 21, 23, 29, 30. Total 8.
- ⛔ Bloqueado: 33. Total 1.

Sem merge, deploy, cobrança, publicação, alterações em segredos ou SQL de produção nesta branch. O fato de haver artefato QA ou PR draft não significa homologação operacional.
