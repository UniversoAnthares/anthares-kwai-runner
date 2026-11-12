# CORTES TikTok — origem recente priorizada e publicação real confirmada

STATUS: PROVEN
AREA: tiktok-publish
SOURCE: cOhqEaY3-08
DATE_UTC: 2026-11-12
LEASE: test-hub/findings/lease-20261111-tiktok-source-birth-queue.md
LEASE_STATE: CLOSED

## Defeito verificado
O consumo anterior selecionava a fonte cujo último item tinha o maior `created_at`. A reposição dos vídeos históricos A7BsgCe3-oo em 2026-11-11 22:12 UTC ultrapassava a fonte atual cOhqEaY3-08, ingressada às 20:42 UTC. Isso retardava a publicação dos cortes da transmissão atual.

## Correção implantada
- PR #2374 integrado ao main, commit `1123d76286f0b28d6712c20aa2ac08e521d3b514`; serviço `infra/neon-cortes-tiktok/index.mjs` agora prioriza a fonte pela menor data de criação de seus itens, condicionada a haver itens `queued` cujo retry já venceu. Preserva `FOR UPDATE SKIP LOCKED`, advisory lock, `lease_generation`, cadência de 180–240 s, limite diário de 100 e reconciliação de `uncertain`.
- GitHub PR CI [43134205437](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43134205437): 7 testes Node PASS, 0 FAIL e 57 testes Python PASS.
- Neon Functions main `br-crimson-unit-b89nau08`, função `cortestiktok` versão **14** deployed `completed` e `active`, em 2026-11-12 01:27:38 UTC. Health público respondeu HTTP 200: `service=cortes-tiktok-neon`, `ok=true`, `fencing=true`, `db_ledger_total=635`.
- Fluxo real de consumo [43134715179](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43134715179) confirmou conta `universo.anthares` e primeiro post da fonte atual `g1:cOhqEaY3-08:5:45` às 2026-11-12 01:32:26.657Z: remote_id `7707091633241640212`, URL `https://www.tiktok.com/@universo.anthares/video/7707091633241640212`, estado `confirmed` no ledger.
- Segundo post da mesma fonte `g1:cOhqEaY3-08:45:91` às 2026-11-12 01:37:12.953Z: remote_id `7707092227910143284`, URL `https://www.tiktok.com/@universo.anthares/video/7707092227910143284`, ledger `confirmed`. Fila da fonte atual: 2 confirmados, 67 enfileirados após essas duas provas.
- PR #2376 integrado, commit `4023ef10c7b79308295ec49094884b325a16b56e`: mesma seleção no fallback `vercel-ara-primary/api/cortes-tiktok.mjs`. A execução isolada [43136110077](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43136110077) aprovou 8 testes Node, 0 FAIL e `node --check` em ambos os serviços. A Vercel do projeto está sem prova de publicação da atualização; o backend ativo e confirmado é o Neon v14.

## Controles e limitações
- Nenhum vídeo incerto recebeu retry, nenhuma credencial foi exposta, nenhum checkpoint de publicação foi editado diretamente por SQL.
- Os 159 segmentos ainda sem arquivo final continuam dependentes de recuperação autorizada do vídeo-fonte; YouTube retornou `LOGIN_REQUIRED` em navegadores hospedados e a credencial `YOUTUBE_COOKIES` do job hospedado passou por `COOKIE_FORMAT_UNVERIFIED`.
- Os 67 cortes atuais restantes seguem sob o limitador de publicação e o executor de nuvem já existente.
- Em caso de novos backfills, monitorar origem efetivamente selecionada e auditar `status/remote_id` pelo Neon.

**CLOSED:** prioridade TikTok da fonte recente e primeiro/segundo post real da fonte cOhqEaY3-08. **OPEN fora deste lease:** ingestão dos 159 segmentos sem master, outras redes, publicação dos 67 restantes, estado de fallback Vercel.
