# Item 10 — resíduos da arquitetura local aposentados
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-06
SUPERSEDES: test-hub/findings/20261006-0643-lease-architecture-local-runtime-cleanup-item10.md; test-hub/findings/20261006-0702-lease-architecture-local-runtime-cleanup-item10-renewal.md

## Resultado
As rotas operacionais foram auditadas e endurecidas para impedir dependência ou seleção do PC do usuário. Código histórico/testes continuam permitidos somente quando não participam da produção.

## Resíduos removidos/neutralizados
- Defaults Windows `D:\\AntharesWork\\...` removidos de `direct-tiktok-publisher/publisher_common.py`; estado efêmero agora usa `ANTHARES_RUNTIME_STATE_DIR`, `RUNNER_TEMP` ou temp do executor cloud.
- `direct-tiktok-publisher/tiktok_web_publish_local.py`, que já rodava no GitHub-hosted runner mas carregava nomenclatura da fase local, foi renomeado para `tiktok_cloud_publish.py`; o workflow de produção foi atualizado e não resta referência ao nome antigo.
- Branch morto `kwai_live && id==local` removido do seletor.
- Rota genérica de job agora rejeita executores aposentados, inclusive quando o chamador possui autenticação administrativa.
- Heartbeat rejeita executores aposentados com HTTP 410.
- `local`, `pc`, `windows`, `oracle`, `google`, `google_compute` ficam em `RETIRED_EXECUTORS` e nunca aparecem nas prioridades.

## Varredura operacional
Busca versionada fora de findings/tests/ai-runners retornou zero ocorrências operacionais de:
- MEmu;
- `LOCAL_EXECUTOR_*`;
- Cookie Bridge;
- `C:\\Users\\...`;
- `D:\\AntharesWork\\...`;
- runner `self-hosted`;
- runner Windows;
- `schtasks`/tarefas agendadas Windows;
- `tiktok_web_publish_local`.
Também não há referência operacional a PowerShell daemon.

## ADB e loopback classificados corretamente
ADB permanece em workflows `runs-on: ubuntu-24.04`/`ubuntu-latest` e é Android cloud, não ADB do PC. Os únicos `127.0.0.1` relevantes fora de testes são:
- mock isolado de QA de queue adapter;
- `kwai_remote_android_login.sh`/`kwai_remote_android_ui.py`, onde o loopback liga um servidor dentro do próprio GitHub-hosted runner a um tunnel cloudflared. O chamador `kwai-android-runner.yml` usa `runs-on: ubuntu-24.04`.
Esses caminhos não alcançam nem exigem o computador do usuário.

## Guard permanente
Novo `tests/test_cloud_only_runtime.py` varre superfícies operacionais e falha se MEmu, LOCAL_EXECUTOR, Cookie Bridge, caminho do PC, runner Windows/self-hosted, tarefa Windows ou o nome do publicador local forem reintroduzidos. Também exige a lista RETIRED_EXECUTORS, prioridades cloud-only e sinais de failover/recovery.
`.github/workflows/control-plane-static-safety.yml` roda esse teste automaticamente quando o Worker, publisher/rotas relevantes ou o próprio guard mudam.

## Provas
- Local/static: `CLOUD_ONLY_RUNTIME=PROVEN`, Node syntax e Python compile passaram.
- Produção: seis IDs aposentados (`local`, `pc`, `windows`, `oracle`, `google`, `google_compute`) retornaram HTTP 410 em `/heartbeat`; `/job/enqueue-local` retornou 410.
- GitHub-hosted fresh checkout: `Control Plane Static Safety Validation` run `37453759746`, job `safety`, `success`, incluindo `DEPLOYED_CLOUD_ONLY_FAILOVER=PROVEN`.
- Código principal: `68cc5211897701747d0abfb6a52b9320eec9fc81`; pós-deploy assertion: `fbd4061ac63e4fe025b8f6d8e7aaba91e8917b43`.

## Conclusão
Item 10 fechado. Não há rota operacional capaz de escolher ou exigir o PC do usuário. ADB/loopback que permanecem são internos a executores cloud e estão cobertos por guard automatizado.