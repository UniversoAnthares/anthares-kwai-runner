# ARA — operational handoff (2026-10-14)

## Fonte de verdade atual

O desenho com múltiplos executores/supervisores HTTP foi superado pela Fase 4. Não use estado histórico para restaurar o sistema.

Runtime canônico do Windows:

- dispositivo: `DESKTOP-FTDK0HP`;
- uma única instância de `anthares-remote-agent-v4.exe`;
- identidade `SYSTEM`, sessão 0;
- tarefa `Anthares Remote Agent SYSTEM`;
- código/binários em `C:\ProgramData\AntharesRemoteAgent`;
- trabalho, logs, jobs e estado em `D:\AntharsWork`;
- supervisor: `run-agent-system-supervisor.ps1`;
- recuperação: `recovery-watchdog-loop.ps1` -> `recovery-watchdog.ps1`;
- transportes simultâneos no mesmo processo: private issue queues + HTTP MCP secundário.

As filas GitHub/GitLab são a rota independente de recuperação. O HTTP `anthares-ara-backup.anthares1.workers.dev` existe no mesmo V4 apenas para baixa latência das ferramentas ChatGPT e não cria segundo executor.

## Aceitação de uma instalação/cutover

Nunca aceite apenas “processo está rodando”. `install-system-v8.ps1` deve comprovar:

1. scripts canônicos válidos e com `.lastgood`;
2. V4 validado com baseline;
3. credencial DPAPI LocalMachine carregável pelo SYSTEM;
4. V4 em sessão 0;
5. job real `agent_health` pela fila GitHub;
6. resultado do mesmo job com `ok=true`, `queue_configured=true`, `http_control=true` e dispositivo correto;
7. somente depois disso executores antigos são desativados.

`phase4-migrate-task.ps1` só aceita `queue_end_to_end_proof=true`, `mcp_http_transport_configured=true` e PID SYSTEM válido.

## Recuperação

O watchdog local continua sendo a redundância fundamental. Ele:

- mantém as tarefas SYSTEM;
- restaura V4 e scripts críticos por `.lastgood`;
- verifica credencial privada;
- elimina agentes fora da sessão 0;
- registra estado explícito;
- mantém o V4 vivo via fila mesmo quando o HTTP está indisponível.

A falha do Cloudflare não deve encerrar o processo quando a fila estiver configurada. A recuperação pela fila não depende de Render, Cloudflare, Northflank, MeshCentral ou WinRemote.

## Compatibilidade HTTP antiga

`run-agent-supervisor.ps1` e `run-agent-standard.ps1` não são o HTTP integrado do V4. São launchers legados de break-glass e exigem `C:\ProgramData\AntharesRemoteAgent\allow-http-compat.flag`. Sem o flag, saem sem iniciar agente.

Render permanece somente último fallback de emergência nesses launchers; nunca primário, requisito ou autoridade de estado.

## Caminhos aposentados

- self-hosted installer antigo: fail-closed;
- bootstrap público: HTTP 410;
- dual HTTP watchdog: aposentado;
- user-session fallback: apenas desativa executor de usuário;
- qualquer tarefa apontando para `D:\AntharsWork\AntharesRemoteAgent\*.ps1`: incorreta;
- `DESKTOP-FTDK0HP-SYSTEM` como device ID separado: histórico.

## Diagnóstico

Use `agent_health` antes de shell. Ele retorna estado não secreto dos dois transportes e do PID. Depois valide uma operação real através do conector Anthares Remote do ChatGPT. `session_status` HTTP 200 isolado não basta.

## CI

`Publish ARA V4 recovery binary` deve passar:

- Phase 4 invariant guard;
- Go tests;
- Windows amd64 build;
- stable recovery release publish.

A guarda impede raiz persistente em `D:`, bootstrap mutável, self-hosted installer legado, dual supervisor, HTTP legado sem break-glass, perda do dual-transport canônico e cutover sem prova real.

## Critério de saúde

Só declarar Anthares Remote saudável quando houver, na instalação atual:

- prova real de fila respondida pelo V4 SYSTEM/session 0; e
- comando real recente feito pelo conector Anthares Remote conectado no ChatGPT.
