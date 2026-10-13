# Fase 0 — Auditoria operacional

Status: PASSED
Data da auditoria: 2026-10-13
Dispositivo: DESKTOP-FTDK0HP

## Arquitetura canônica fixada

O Anthares Remote canônico é o `anthares-remote-agent-v4.exe` executado em Session 0 sob SYSTEM. O supervisor canônico é `C:\ProgramData\AntharesRemoteAgent\run-agent-system-supervisor.ps1`. O transporte canônico configurado no momento é a private issue queue do GitHub `UniversoAnthares/anthares-ara-queue`. GitLab existe como projeto de redundância, porém ainda não está configurado no supervisor (`gitlab_queue=false`). Render, Cloudflare e demais control planes HTTP ficam fora do transporte canônico do V4.

## Processos reais observados

- Supervisor SYSTEM: PowerShell PID 17088, Session 0, filho do serviço de tarefas (`svchost.exe` PID 1820).
- Agente canônico: `anthares-remote-agent-v4.exe`, Session 0, filho do supervisor PID 17088. O PID muda durante a auditoria: 6980 às 19:22Z e 23308 às 19:28Z. Portanto o V4 sofre reinícios recorrentes e o supervisor o relança.
- Agente HTTP legado/administrativo: `anthares-remote-agent.exe` PID 17344, Session 3, usuário Lucas. Seu pai original PID 23020 já não existe. Este processo atende os jobs do canal HTTP usado pelo Anthares Remote desta sessão e cria subprocessos em `C:\ProgramData\AntharesRemoteAgent\jobs\...`.
- Bridge GitHub legado: PowerShell PID 32084, Session 3, usuário Lucas, iniciado pela tarefa `Anthares-GitHub-Queue-Bridge`.
- Executor Kwai local: processo Python separado, fora da raiz do ARA canônico.

## Tarefas e persistência

A conta do agente HTTP/usuário não possui permissão para consultar diretamente as tarefas SYSTEM: `schtasks /Query` para `Anthares Remote Agent SYSTEM` e `Anthares Remote Recovery Watchdog` retorna `Acesso negado`. A ausência dessas tarefas na enumeração feita pela conta de usuário não significa ausência no Task Scheduler.

O watchdog em contexto SYSTEM grava continuamente `C:\ProgramData\AntharesRemoteAgent\recovery-watchdog-state.json`. Na auditoria ele registrou:

- `canonical_task_present=true`
- `canonical_task_state=Running`
- `canonical_principal=SISTEMA`
- `canonical_runlevel=Highest`
- `system_agent_count=1`
- `github_queue=true`
- `gitlab_queue=false`
- `dual_queue_redundancy=false`

O arquivo de estado continuou sendo atualizado durante a auditoria (ex.: 19:26:30Z), comprovando execução recorrente do watchdog.

O `recovery-watchdog.ps1` instalado cria/repara `Anthares Remote Agent SYSTEM` com:

- `New-ScheduledTaskTrigger -AtStartup`
- principal `SYSTEM`
- `LogonType ServiceAccount`
- `RunLevel Highest`
- `RestartCount 999`
- `RestartInterval 1 minute`
- `StartWhenAvailable`
- `MultipleInstances IgnoreNew`
- `ExecutionTimeLimit = 0`

O teste efetivo de reboot permanece reservado à Fase 15; a Fase 0 estabelece qual mecanismo deve sobreviver a logoff/boot e confirma que ele está ativo agora.

### Tarefas visíveis na sessão do usuário

- `Anthares Remote Agent User`: Disabled; usuário Lucas; LogonType Interactive; RunLevel Limited; `IgnoreNew`.
- `Anthares-GitHub-Queue-Bridge`: Running; usuário Lucas; LogonType Interactive; RunLevel Limited; `IgnoreNew`; trigger de logon + trigger temporal.
- `Anthares Kwai Local Executor`: Ready; usuário Lucas; trigger de logon; último resultado 1.

## Descoberta crítica sobre o bridge GitHub legado

A tarefa `Anthares-GitHub-Queue-Bridge` aponta para:

`D:\AntharsWork\AntharesRemote\github-queue-bridge.ps1`

O diretório `D:\AntharsWork\AntharesRemote` não existe mais. O processo PowerShell já iniciado continua em memória, enquanto novos relançamentos da tarefa apontam para um arquivo ausente. O `LastTaskResult` observado foi `2147946720`. Esse bridge é um potencial consumidor concorrente da mesma fila GitHub e deve ser tratado na Fase 2 (single writer), depois da estabilização da raiz SYSTEM na Fase 1.

## Transporte e estado do V4

O estado canônico em `D:\AntharsWork\legacy-pc-runtime\supervisor\system-supervisor-state.json` foi atualizado durante a auditoria e declarou:

- `active_control=private-issue-queues`
- `mode=issue-queues-only`
- `identity=AUTORIDADE NT\\SISTEMA`
- `session=0`
- `binary=anthares-remote-agent-v4.exe`
- `github_queue=true`
- `gitlab_queue=false`
- `render_required=false`
- `cloudflare_required=false`
- `http_control_enabled=false`

O stdout do V4 confirmou `Anthares issue queue enabled providers=1 interval=20s`.

O stderr mostrou tentativas contra `https://ara-control-unavailable.invalid/...`. Esse endpoint inválido é usado para impedir dependência de um controlador HTTP; entretanto o binário ainda executa seu liveness guard HTTP e isso coincide com a troca recorrente de PID do V4. Essa instabilidade entra na Fase 1.

A fila GitHub estava funcional em testes anteriores da mesma tarde: issues #36, #37 e #38 chegaram a `ara-completed`. Durante esta auditoria foram criadas as issues #40 (auditoria SYSTEM) e #41 (ping curto); ambas permaneceram sem resultado durante a janela observada. Essa condição entra na Fase 3 depois da estabilidade do V4.

## Estado GitLab

Projeto real confirmado: `universo-anthares-group/anthares-kwai-runner`, projeto privado GitLab ID 87307279. O suporte de configuração existe no `load-issue-queue-auth.ps1`, com credenciais DPAPI LocalMachine para GitHub e GitLab. O supervisor atual informa `gitlab_queue=false`. A ativação e o failover pertencem às Fases 5 e 6.

## Arquivos críticos instalados

SHA-256 local:

- `run-agent-system-supervisor.ps1`: `0C3893C648D6B38184CC5F0888B4B61BB4ACD0788D514D78737F96ED0161D268`
- `recovery-watchdog.ps1`: `0DCB952865A1A319FDE2FB8ED29ACC38CE70EB67B621FDB67D8F0D188E1B314E`
- `load-issue-queue-auth.ps1`: `80BBCC64448F5957296BFB328CEC41465E9C5A716653913A020ADFF0789149FE`
- `run-agent-user-fallback.ps1`: `9FFE4951A7923CB8554B6E5AFA360E8CDB91A96D5C589D2ACA4B1E6E188713F5`
- `run-agent.ps1`: `2E2F08F5165AE435E08DC058E483157A3273859B6F1AC00D1AED7043724A2B12`
- `anthares-remote-agent-v4.exe`: `2A82EF40ECC3BA1FCDF0022711B740B211542D2A96BDAF2087B2DCC4B873CE19`
- `anthares-remote-agent.exe`: `5856A818EB584D3C69AED19CF32EEEA46BB4E96BD4171872D5F0B21FADE94993`

Comparação Git blob local × `main`:

- `load-issue-queue-auth.ps1`: corresponde ao `main` (`e00b5b10db73ee51083ed5974dc773c64a02de2c`).
- `run-agent-user-fallback.ps1`: corresponde ao `main` (`8cd40d722d1cf70acf97de2f0685c544fca58710`).
- `run-agent-system-supervisor.ps1`: instalado diverge do `main` (local `f6e61a67e9422fc3fd6ac1ed452ddcf047cf023c`; `main` `a48cb60482f86eeb5a99b693220ab93a7f47a8c2`).
- `recovery-watchdog.ps1`: instalado diverge do `main` (local `864024f2d2556a8d4f085465b54c20af8408aee2`; `main` `d09ea7b33967ad35c96f3db927d47c807cac8f55`).

Essa deriva é registrada para a Fase 4; nenhum arquivo operacional foi substituído na Fase 0.

## Estados antigos que não são fonte de verdade

Existem arquivos históricos em `C:\ProgramData\AntharesRemoteAgent` que ainda mencionam Render, Cloudflare e supervisores antigos (`supervisor-state.json`, `standard-supervisor-state.json`, `system-supervisor-state.json`). Seus timestamps são anteriores ao estado canônico de `D:\AntharsWork\legacy-pc-runtime\supervisor\system-supervisor-state.json`. Eles devem ser tratados como artefatos históricos até a consolidação posterior.

Existe também um antigo `D:\AntharsWork\legacy-pc-runtime\ara\user-fallback-state.json` da sessão de Lucas. A tarefa `Anthares Remote Agent User` está desabilitada e os PIDs registrados nesse arquivo já não são os processos canônicos atuais.

## Matriz de autoridade atual

| Função | Componente | Estado | Autoridade atual |
|---|---|---|---|
| Supervisor ARA canônico | `run-agent-system-supervisor.ps1` | ativo | SYSTEM / Session 0 |
| Executor ARA canônico | `anthares-remote-agent-v4.exe` | ativo, reiniciando | SYSTEM / Session 0 |
| Transporte canônico | GitHub private issue queue | configurado | V4 |
| Transporte redundante | GitLab private queue | ainda desativado | futuro V4 |
| Canal HTTP administrativo | `anthares-remote-agent.exe` | ativo | usuário / Session 3 |
| Bridge GitHub legado | `github-queue-bridge.ps1` | processo ativo; arquivo de origem ausente | usuário / Session 3 |
| User fallback | `run-agent-user-fallback.ps1` | tarefa desabilitada | usuário / Session 3 |
| HTTP HA Vercel/Neon/Northflank/Render | auxiliar | fora do caminho canônico | fases posteriores |

## Pendências encaminhadas sem criar novas fases

1. Fase 1: estabilizar a raiz SYSTEM e impedir os reinícios recorrentes do V4; preservar AtStartup/SYSTEM/Highest/hidden/self-healing.
2. Fase 2: retirar o bridge GitHub legado e qualquer outro consumidor concorrente somente depois de provar substituição; alcançar single writer real.
3. Fase 3: validar o protocolo GitHub ao vivo, incluindo as issues #40/#41 pendentes, exatamente uma resposta e antirreplay.
4. Fase 4: sincronizar no repositório as versões efetivamente instaladas do supervisor e watchdog depois que a configuração operacional for aprovada.
5. Fases 5-6: ativar GitLab e provar failover/dedupe cross-provider.

## Critério da Fase 0

A fonte de verdade operacional está identificada. Sabemos qual supervisor inicia o V4, qual tarefa assegura boot, qual processo é o executor SYSTEM, qual canal HTTP permanece separado, qual componente legado ainda toca a fila GitHub, quais transportes estão configurados, quais arquivos locais divergem do repositório e quais estados antigos devem ser ignorados. Nenhuma limpeza ampla foi executada.

Fase 0: PASSED.
Próxima fase obrigatória: Fase 1 — restaurar/estabilizar a raiz de persistência SYSTEM.