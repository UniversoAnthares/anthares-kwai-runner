# CORTES: janelas de publicação obrigatórias — 06h00 inclusive, 23h00 exclusive

STATUS: PROVEN_WITH_RUNTIME_CADENCE_PENDING
AREA: tiktok-primary / tiktok-secondary / all-social-publishing / pacing-hard-guard
DATE: 2026-11-12
RUNS: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43281654949 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43281663419 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43285263916
JOBS: CORTES TikTok per-account proportional pacing contract; CORTES proportional deadline pacing source contract
COMMITS: anthares-kwai-runner PR #2435 f057fa805695c56951ae5ffe9e5ede5bf1275efc; PR #2440 ee9ab612d68e7ec56840959c83c7e02964a35fe8; anthares-wordpress PR #267 8d854424a659ac4de1de89de0deadcdc052aa27a
SUPERSEDES: test-hub/findings/20261112-cortes-proportional-hostinger-neon-live-proven.md

## Incidente comprovado

Em 2026-11-12, no fuso America/Campo_Grande, o ledger canônico de `tiktok:universo.anthares` confirmou **100** publicações de 00:01:49 a 09:38:45. As 100 ocorreram antes da implantação da política proporcional do TikTok principal, deployment Neon #15, instalada às 13:13 local. A rotina anterior usava espaçamento fixo 180–240 segundos e limite de horário 23:45. Um endpoint Vercel adicional (`anthares-remote-primary`) ainda apontava para commit de outubro com esse espaçamento. Nenhum dos 100 envios foi refeito, apagado ou fingido como falha.

## Política permanente, por plataforma e conta

- Janela dura para iniciar publicações: `06:00:00 <= hora_local < 23:00:00`, timezone `America/Campo_Grande`.
- Primeiro corte elegível do dia: devido no primeiro despertador/executor após 06h; sem agendamento à meia-noite.
- Demais: espaçamento recalculado após cada confirmação real conforme `(22:59:00 - max(ultimo_confirmado,ultimo_iniciado))/quantidade_ainda_elegivel_na_cota`.
- Último slot planejado: 22h59; às 23h a liberação de novas publicações cessa até o dia seguinte.
- Controle de limite por conta/plataforma, retenção de estados `uncertain` e limite real de provedor. Cron apenas desperta o consumidor e jamais define a cadência de postagem.
- Falha fechada se ledger, identidade, hora, cota ou proteção independente não puderem ser comprovados.

## Duas barreiras independentes na origem e uma barreira no banco

1. `infra/neon-cortes-tiktok/index.mjs`, `infra/neon-cortes-lucasrosalem4/index.mjs`: cálculo a partir de timestamps reais, 06h / 22h59 / 23h, validações em GET NEXT e no STARTED. `tools/cortes_deadline_pacing.py`: regra genérica Python com validação final.
2. `infra/neon-cortes-queue/index.mjs` e `infra/neon-cortes-threads-execution/index.mjs`: mesmas fronteiras para redes/contas comuns, inclusive Threads em nuvem e consumidor local consultando Neon. WordPress: `anthares_cortes_proportional_deadline()` e `anthares_cortes_pacing_assert_due()`, com histórico de `last_started_at` em Instagram, Threads e Facebook; `anthares_cortes_short_schedule()` não gera horários fora da janela.
3. **Barreira transacional independente do código cliente:** migração aditiva `db/migrations/20261112_tiktok_hard_window_proportional_guard.sql`, função `cortes_tiktok_proportional_start_guard_20261112()`, gatilhos `cortes_tiktok_hard_window_06_23_v1` e `cortes_tiktok4_hard_window_06_23_v1`. Instalados no Neon de produção `purple-flower-35918989/br-crimson-unit-b89nau08` em 12/11; `SELECT pg_get_triggerdef` comprovou os dois BEFORE UPDATE. Examinam a janela, lease, primeiro/último registro, próximos horários, quota e serializam pela conta/dia. Uma tentativa antiga de STARTED fora da janela gera SQLSTATE 23514, reverte a transação e preserva o orçamento.

## Implantação e testes

- Neon QA `br-silent-mud-b8fzvqta`: ambos os gatilhos instalados e lidos; quatro serviços com novos pacotes e health GET positivos.
- Neon produção: `cortestiktok` deployment **16**, `cortestiktok4` deployment **7**, `cortesqueue` deployment **69**, `cortesthreadspub` deployment **16**; todos `completed` e GET saúde positivos. Source GitHub da função central passou a SHA blob `922055b46b9e115661b0639f3eb08d5231d90978`, preservando correções concorrentes após o merge original.
- WordPress Hostinger: cinco arquivos instalados da PR #267, com SHA256 conferidos, PHP 8.2 lint em staging e produção, plugin ativo e teste WP-CLI `CORTES_WP_06_TO_23_RUNTIME_QA=PASS` verificando 05:59 bloqueado, 06:00 devido, horário proporcional, 22:59 último slot, 23h bloqueado e iniciado sem confirmação sem rajada. Backup privado: `/home/u566597497/domains/anthares.us/.anthares-deploy-backups/cortes-06-to-23-20261112`.
- GitHub CI: Node tests PASS (06h, 23h, last_started, DB guard e fallback), Python 20/20 PASS, regressão do consumer stale-Vercel PASS.
- Vercel produção: projeto `anthares-remote-primary` está preso à implantação de outubro. Tentativa de atualização via Vercel API foi negada por **402 resource_creation_blocked**, fair-use da equipe Hobby; não alterar billing/plan. PR #2440 elimina essa Vercel antiga dos backends mutáveis do consumidor TikTok principal. **Preserva seu endereço apenas como audience OIDC**, e usa Neon canônico + HA Cloudflare, ambos com health `ok=true,fencing=true`. O guard PostgreSQL bloqueia qualquer tentativa eventual da Vercel antiga.

## Prova que ainda depende de evento futuro

Como a conta principal já tinha 100/100 inícios em 12/11, não há autorização para novo vídeo no próprio dia. Às 14:59 MS, Neon reportou 46 itens `queued` nesta conta, e 2 gatilhos de janela instalados. O primeiro envio após as 06h de 13/11 e o segundo horário proporcional precisam ser comprovados pelas respectivas confirmações futuras; essa observação não integra o resultado de QA. Não declarar essa sequência futura como já realizada.

FAILURE_SIGNAL: qualquer transição `publication_started_at` antes 06:00 ou a partir 23:00 local, tentativa antes do `next_due_at`, desaparecimento dos triggers SQL, 100 publicações concentradas novamente pela manhã, ou retorno da Vercel antiga como backend mutável.
SUCCESS_SIGNAL: nenhuma nova transição fora da janela; primeira publicação diária no primeiro acionamento elegível após 06h e demais distribuídas até 22h59, respeitando limitações reais.
