# Anthares Remote Agent

Anthares Remote é o canal canônico de administração remota do Windows do projeto Anthares. O runtime normal não depende de Render, Cloudflare, Northflank, AI Commander, MeshCentral ou Desktop Commander para executar comandos no PC.

## Runtime canônico no Windows

Dispositivo: `DESKTOP-FTDK0HP`.

Existe **um único executor canônico**:

- tarefa: `Anthares Remote Agent SYSTEM`;
- identidade: `SYSTEM`, `Highest`;
- sessão: `0`;
- instalação executável: `C:\ProgramData\AntharesRemoteAgent`;
- trabalho/logs/jobs/estado: `D:\AntharsWork`;
- supervisor: `windows/run-agent-system-supervisor.ps1`;
- recuperação: `windows/recovery-watchdog-loop.ps1` -> `windows/recovery-watchdog.ps1`;
- transporte normal: filas privadas GitHub/GitLab.

`D:\AntharsWork\AntharesRemoteAgent` pode existir como área de staging histórica, mas **não é uma raiz válida para tarefas ou supervisores persistentes**.

## Transporte e redundância

1. GitHub private issue queue — transporte canônico e prova obrigatória de cutover.
2. GitLab private issue queue — transporte independente redundante.
3. HTTP compatibility — somente modo break-glass, mediante `C:\ProgramData\AntharesRemoteAgent\allow-http-compat.flag`.
4. Dentro do modo break-glass HTTP, Cloudflare/Northflank podem ser usados; Render permanece apenas como último fallback de emergência enquanto existir.

O runtime SYSTEM queue-only não precisa de `ANTHARES_CONTROL_URL`.

## Regras de cutover

`windows/install-system-v8.ps1` é o único instalador canônico. Ele só conclui quando todas estas condições forem verdadeiras:

- scripts canônicos sincronizados e parseados;
- `.lastgood` criado para scripts críticos;
- binário V4 validado e com baseline de hash;
- credencial DPAPI LocalMachine das filas carregável pelo SYSTEM;
- `anthares-remote-agent-v4.exe` ativo em sessão 0;
- um job real `agent_health` atravessa a fila GitHub e retorna resultado válido;
- somente depois da prova real executores/tarefas antigas são desativados.

`windows/phase4-migrate-task.ps1` apenas prepara o binário e delega ao instalador canônico. Em falha, restaura o binário anterior e não declara migração concluída.

## Recuperação local

O watchdog roda em SYSTEM e é independente dos serviços de controle externos. Ele:

- garante as tarefas SYSTEM canônicas;
- impede executor Anthares em sessão interativa;
- valida a credencial privada sem imprimir segredos;
- restaura o V4 a partir de `anthares-remote-agent-v4.lastgood.exe` quando o hash diverge;
- restaura supervisor, loader e watchdog a partir de arquivos `.lastgood` quando ausentes ou alterados;
- registra estado explícito, incluindo `queue_credential_present`, `queue_credential_loaded`, `system_v4_count` e `interactive_agent_count`.

## Diagnóstico

Prefira jobs tipados a shell. `agent_health` retorna estado não secreto do executor: PID, dispositivo, work root, transportes configurados, providers de fila e contagem de receipts. `ping`, `system_info`, `safe_environment`, arquivos, processos, serviços e demais capacidades tipadas continuam disponíveis. Shell é escape hatch e deve permanecer oculto/não interativo.

## Caminhos legados aposentados

- `.github/workflows/anthares-remote-agent-install-selfhosted.yml` não instala mais nada e falha fechado.
- `infra/anthares_remote_bootstrap.py` responde 410 e não executa mutações.
- `windows/watchdog-dual-supervisor.ps1` não inicia supervisores legados.
- `windows/run-agent-supervisor.ps1` e `windows/run-agent-standard.ps1` exigem `allow-http-compat.flag`.
- `windows/run-agent-user-fallback.ps1` desativa o executor de usuário.

Nenhum desses caminhos pode ser tratado como runtime canônico.

## Segurança e invariantes

- nenhuma porta de entrada no PC;
- somente conexões HTTPS de saída;
- nenhum token ou segredo em repositório/logs/resultados;
- credenciais de fila persistentes via DPAPI LocalMachine e ACL de SYSTEM/Administrators;
- um executor por dispositivo para evitar comandos/receipts duplicados;
- writes ambíguos não são repetidos automaticamente;
- nenhuma janela visível de PowerShell/CMD;
- Render nunca é primário, obrigatório ou autoridade de estado;
- Cloudflare não é requisito para o executor queue-only;
- CI deve falhar se essas invariantes forem revertidas.
