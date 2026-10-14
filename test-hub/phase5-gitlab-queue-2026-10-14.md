# Fase 5 — Ativação da fila GitLab

Status: BLOCKED_ONLY_ON_LOCAL_GITLAB_TOKEN
Data: 2026-10-14
Dispositivo: DESKTOP-FTDK0HP

## Escopo

Ativar GitLab como segundo transporte privado de issues no mesmo `anthares-remote-agent-v4.exe` SYSTEM/Session 0. O failover/dedupe cross-provider permanece para a Fase 6.

## Estado comprovado

- V4 SYSTEM está saudável; GitHub queue segue operacional.
- Projeto GitLab confirmado: `universo-anthares-group/anthares-kwai-runner` (ID 87307279), privado.
- Label `ara-queued` existe no projeto GitLab.
- Suporte GitLab já existe no V4: polling, validação de autor/envelope, `ARA_RESULT_B64`, remoção de `ara-queued` e adição de `ara-done`.
- `C:\ProgramData\AntharesRemoteAgent\secrets\issue-queue.json` contém `gitlab_project` e `gitlab_author`, mas não contém `gitlab_token_dpapi`; o token GitHub permanece presente.
- Não há `glab`, `GITLAB_TOKEN`, `.git-credentials` ou configuração glab local que possa ser migrada sem criar uma nova credencial.

## Implementação desta fase

- `run-agent-system-supervisor.ps1` agora registra `github_queue`, `gitlab_queue` e `dual_queue_redundancy` no estado operacional.
- `recovery-watchdog.ps1` agora registra os mesmos três campos no estado offline.
- Criado `enable-gitlab-queue.ps1`: valida a credencial contra o projeto privado, preserva o token GitHub existente, grava o token GitLab apenas como DPAPI LocalMachine, restringe ACL para SYSTEM/Administradores, reinicia somente a tarefa canônica SYSTEM e exige as duas filas prontas antes de sucesso.
- O ativador foi instalado em `C:\ProgramData\AntharesRemoteAgent\enable-gitlab-queue.ps1` e passou no parser PowerShell. SHA-256 observado: `E27A29258F79736D41A51EE01083E32B24C2A666326CE18645A3E86B4968D2EB`.

## Prova preparada

GitLab issue confidencial IID 2: `ARA Phase 5 GitLab queue proof 20261014`.

Envelope:

`{"job_id":"fase5-gitlab-queue-proof-20261014","device_id":"DESKTOP-FTDK0HP","type":"ping","args":{},"timeout_seconds":15}`

Label: `ara-queued`.

Critério de conclusão: após provisionar a credencial, o V4 deve consumir o IID 2, publicar `ARA_RESULT_B64` com `ok=true`/`pong`, remover `ara-queued` e adicionar `ara-done`.

## Único bloqueio restante

É necessário criar uma credencial GitLab API para o projeto e fornecê-la localmente ao ativador como `SecureString`. A integração GitLab desta sessão não expõe criação/exportação de token. O valor não deve ser enviado por issue, chat, commit ou log.
