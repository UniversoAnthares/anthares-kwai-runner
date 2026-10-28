# Item fixo 5 — runner AVS Forgejo e recuperação comprovados
STATUS: PROVEN
AREA: architecture/forgejo-ci-runners
DATE: 2026-10-28
RUN: https://anthares.us/forgejo/anthares-admin/anthares-video-studio/actions/runs/3
JOB: Forgejo internal run 296 / task 205
COMMIT: a490d8f05ac801dfcd86e55a14d11ec0bc4ef43a
SUPERSEDES: none

## Escopo e coordenação
Somente runner não publicador de `anthares-admin/anthares-video-studio` na Hostinger existente. Fonte canônica GitHub; AVS segue com produção PAUSED e controles D1/Blob separados. Governança central carregada na revisão `223433740e807a90`; verificação de tarefas AVS em curso retornou zero antes da recuperação. Não houve aquisição de novo plano, mídia, publicação ou ativação de produtor.

BASELINE_PROVEN: Forgejo runner repo-scoped ID 7 `anthares-avs-d1-once-20261028`, rótulos `self-hosted,linux,x64,avs-codespaces-ci`, estava offline, ephemeral=1, e a tentativa anterior de declaração registrou HTTP 403.
FAILED_AVOIDED: job Forgejo run #2 / task 202 obteve alocação mas falhou em `actions/checkout@v4`; não houve reexecução cega desse checkout.
SUCCESS_SIGNAL: `AVS_FORGEJO_RUNNER=PROVEN`, `AVS_FORGEJO_SOURCE_SHA=a490d8f05ac801dfcd86e55a14d11ec0bc4ef43a`, `Job succeeded`, `AVS_RUNNER_RECOVERY=PROVEN`.
FAILURE_SIGNAL: runner sem heartbeat, identidade/escopo incorretos, SHA divergente, task com efeitos incertos, runner duplicado ou retorno não terminal.
TEST_VALIDITY: execução real Forgejo Actions, logs zstd decodificados e estado terminal `action_run.status=1`, `action_task.status=1`, runner_id=7; recuperação real verificada no próprio servidor, não mock/preflight.

## Resultado
1. O registro existente ID 7 foi reconciliado idempotentemente para modo **persistente** (`ephemeral=0`), mantendo a identidade de repositório. Daemon Forgejo v13.2.0 declarou-se com sucesso. Uma segunda instância acidental foi encerrada após conferir a ausência de tarefa nela.
2. PR GitHub AVS #59, incorporada à `main`, adicionou somente `.forgejo/workflows/avs-hostinger-runner-smoke.yml`: manual, offline, sem checkout por CDN, sem credenciais, publicação ou deploy.
3. Espelho GitHub→Forgejo AVS sincronizou em modo já existente, `AVS_GIT_MIRROR=PASS` com SHA acima. Um único `workflow_dispatch` recebeu HTTP 204 e criou run interna 296, job 205, run web #3. Terminal SUCCESS; log: `AVS_FORGEJO_RUNNER=PROVEN`, `AVS_FORGEJO_SOURCE_SHA=...`, `Job succeeded`.
4. A supervisão Hostinger existente `ensure-all.sh` recebeu um hook para `avs-d1-once-20261028/ensure-daemon.sh`, sem novo cron nem interferência nos runners WordPress/TikTok. O helper tem lease `flock`, escopo repo/runner, contagem exata de processos, verificação de heartbeat e bloqueio se houver job em andamento/incerto. `bash -n` passou. SHA256 do helper `32ba1bab6f9b0ec00b8a2980c2e98f676dedaf5afeb3db231144ec4079fdc59c`; SHA256 novo do `ensure-all.sh` `68dc9e83ba2885e88f773a9ed20adaa302ec33042e86295106a70b1185daad76`, com backup privado para rollback.
5. Verificação isolada `AVS_RUNNER=ALIVE` passou. Após conferir zero tarefas AVS ativas, houve uma única interrupção controlada PID 2266452 e restauração via helper PID 3017649. Recibo privado `recovery-proof-20261028.json`: `status=PROVEN`, runner_id=7, `AVS_RUNNER=RECOVERED`, heartbeat atualizado.
6. Runner CI Hostinger `anthares-ci-hostinger-v2` do sandbox já possuía provas independentes de êxito para sete workflows não publicadores (runs 243,245–251), preservadas sem reexecução.

## Limites
Esta homologação conclui a **preparação e execução/recuperação dos runners no escopo do item fixo 5**. Não prova publicação TikTok/X, promoção geral de fallback, execução Android/browser nem admissão produtiva AVS D1/Blob. O cron hPanel existente tinha recibo `PASS` às 22:00 UTC antes do novo hook; a recuperação controlada do helper está comprovada e o hook encontra-se instalado, mas um futuro disparo automático do hPanel não foi simulado.

LEASE: ENCERRADO — alteração de runner e teste único finalizados; nenhuma execução pendente.
