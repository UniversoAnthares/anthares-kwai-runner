# ARA — operational handoff (2026-10-14)

## Fonte de verdade atual

O desenho Render/HTTP de 2026-10-13 foi superado pela Fase 4. Não use aquele estado histórico para restaurar o sistema.

Runtime canônico do Windows:

- dispositivo: `DESKTOP-FTDK0HP`;
- uma única instância de `anthares-remote-agent-v4.exe`;
- identidade `SYSTEM`, sessão 0;
- tarefa `Anthares Remote Agent SYSTEM`;
- código/binários em `C:\ProgramData\AntharesRemoteAgent`;
- trabalho, logs, jobs e estado em `D:\AntharsWork`;
- transporte normal: private issue queues GitHub/GitLab;
- supervisor: `run-agent-system-supervisor.ps1`;
- recuperação: `recovery-watchdog-loop.ps1` -> `recovery-watchdog.ps1`.

Não existe controlador HTTP obrigatório nesse caminho.

## Aceitação de uma instalação/cutover

Nunca aceite apenas “processo está rodando”. `install-system-v8.ps1` deve comprovar, nesta ordem:

1. scripts canônicos sincronizados e sintaticamente válidos;
2. binário e scripts com lastgood/baseline;
3. credencial DPAPI LocalMachine carregável pelo SYSTEM;
4. V4 rodando em sessão 0;
5. job real `agent_health` criado na fila GitHub;
6. `ARA_RESULT_B64` do mesmo job retornado com `ok=true`, `queue_configured=true` e dispositivo correto;
7. só então tarefas/executores antigos podem ser desativados.

`phase4-migrate-task.ps1` deve considerar sucesso somente quando `queue_end_to_end_proof=true` no `install-result.json`.

## Recuperação

O watchdog local é a redundância fundamental porque continua existindo quando todos os serviços externos estão inacessíveis. Ele deve:

- manter as duas tarefas SYSTEM corretas;
- restaurar binário V4 validado;
- restaurar scripts críticos por `.lastgood`;
- verificar carregamento da credencial privada;
- matar agentes Anthares fora da sessão 0;
- registrar estado explícito e não entrar em restart loop quando falta credencial.

## Compatibilidade HTTP

`run-agent-supervisor.ps1` e `run-agent-standard.ps1` são somente break-glass. Eles devem sair sem iniciar agente quando `C:\ProgramData\AntharesRemoteAgent\allow-http-compat.flag` não existe.

Se break-glass for deliberadamente ativado, Render continua somente como último fallback; nunca como origem primária, requisito de autenticação ou autoridade de estado. Remova o flag depois da recuperação.

## Caminhos aposentados

- self-hosted installer antigo: aposentado/fail-closed;
- bootstrap público temporário: HTTP 410, sem execução de comandos;
- dual HTTP watchdog: aposentado;
- user-session fallback: apenas desativa executor de usuário;
- qualquer tarefa apontando para `D:\AntharsWork\AntharesRemoteAgent\*.ps1`: incorreta;
- qualquer documentação que trate `DESKTOP-FTDK0HP-SYSTEM` como device ID canônico separado: histórica.

## Diagnóstico

Use `agent_health` antes de shell. Ele fornece diagnóstico não secreto do executor/transportes e evita depender de saída localizada de `tasklist`, `whoami` ou PowerShell. Use jobs tipados para arquivos/processos/serviços sempre que possível. Shell é escape hatch.

## CI

`Publish ARA V4 recovery binary` deve passar:

- Phase 4 invariant guard;
- Go tests;
- Windows amd64 build;
- stable recovery release publish.

A guarda também impede reativação do bootstrap mutável, self-hosted installer legado, dual supervisor, HTTP sem break-glass, raiz executável em `D:` e cutover sem prova de fila.

## Regra operacional

Não declarar Anthares Remote saudável sem uma execução real recente. Gateway/MCP HTTP 200 não significa executor Windows conectado. A prova mínima do runtime canônico é um job real na private queue respondido pelo V4 SYSTEM/session 0.
