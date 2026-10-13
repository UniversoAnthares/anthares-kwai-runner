# Fase 3 — Protocolo canônico GitHub Issues → ARA V4 SYSTEM

Status: protocolo operacional validado no equipamento DESKTOP-FTDK0HP. Fase 3 não ativa GitLab; redundância de transporte é Fase 5–6.

## Autoridade e transporte

- **Único executor**: `anthares-remote-agent-v4.exe` na sessão 0, supervisionado pela tarefa `Anthares Remote Agent SYSTEM` e pelo recovery watchdog. Não executar outra instância/bridge que consuma a mesma fila.
- **Transporte primário**: repositório **privado** `UniversoAnthares/anthares-ara-queue`, GitHub Issues API por HTTPS.
- **Credencial**: carregada de armazenamento local protegido por DPAPI, sem token no corpo de issues, logs ou CI.
- **Autoria**: aceitar somente o usuário configurado em `ANTHARES_GITHUB_QUEUE_AUTHOR` (ou proprietário do repositório).
- **Seleção**: issues abertas com rótulo `ara-queued`. Uma issue = uma solicitação; não editar o corpo depois da submissão.
- **Intervalo**: 20 segundos, configurável entre 10 e 300.

## Envelope (JSON estrito)

```json
{"job_id":"exemplo-20261013-001","device_id":"DESKTOP-FTDK0HP","type":"ping","args":{},"timeout_seconds":15}
```

Campos permitidos: `job_id` (único, estável e seguro para nome de arquivo), `device_id` (identidade exata do executor), `type` (capacidade implementada), `args` (mapa string→string) e `timeout_seconds` (0–120; 0 usa padrão de 30). Campos desconhecidos são rejeitados, assim como dispositivo incorreto. Não colocar segredos em `args`: o corpo da issue é persistente.

## Resultado e confirmação

- O agente registra um recibo persistente **antes** de executar, usando criação exclusiva, em `ANTHARES_ISSUE_QUEUE_STATE_DIR` ou `ANTHARES_WORK_ROOT/ara-jobs/issue-queue`.
- O recibo associa `job_id`, estado, origem, horários e resultado. O mesmo `job_id` não é executado novamente.
- O resultado é JSON codificado em Base64, publicado em comentário(s) `ARA_RESULT_B64 part=N/T`; o agente remove `ara-queued` após a publicação.
- Um recibo `started` sem resultado após interrupção vira **uncertain** e não é reexecutado automaticamente. Operações de efeito colateral exigem reconciliação antes de novo ID.
- `job_id` deve ser globalmente único também entre GitHub e futura fila GitLab; compartilhar diretório de recibos entre transportes.
- Comentários repetidos são possíveis se a API aceitar a postagem e falhar antes da remoção do rótulo; consumidores devem deduplicar por `job_id`, não contar comentários como execuções.
- Não apagar recibos para forçar replay. Em falha de API, manter issue pendente e repetir a confirmação, nunca o comando.

## Capacidade e limites

- `type` é despachado somente por capacidades implementadas; operações mutáveis respeitam raízes e executáveis autorizados.
- A execução do job tem timeout máximo de 120 segundos.
- Sem HTTP control plane, sem janela interativa, sem PowerShell/CMD visível. O controle da fila não depende de Render nem Cloudflare.
- Logs devem omitir tokens, payloads sensíveis e conteúdo de clipboard.

## Prova prática

- Issue [#50](https://github.com/UniversoAnthares/anthares-ara-queue/issues/50): resposta única `ok=true`, `output=pong`, rótulo `ara-queued` removido, executado pelo V4 atualizado.
- Fase 2: usuário confirmou somente `anthares-remote-agent-v4.exe` na sessão 0.
- Esta prova confirma o transporte primário, **não** prova failover GitLab, reinício do Windows ou execução de outros tipos de job.

## Próxima fase

Fase 4: sincronizar binário e scripts instalados com o repositório, preservando backup, hash e rollback. Fases 5–6: configurar segundo transporte GitLab e validar failover sem execução duplicada.
