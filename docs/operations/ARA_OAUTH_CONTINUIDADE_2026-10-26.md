# Anthares Remote — incidente OAuth e garantia operacional

Data da investigação: 2026-10-26 (UTC). Escopo: Cloudflare MCP, Vercel/Neon, agente Windows e autorização do proprietário pelo GitHub.

## Diagnóstico verificado

- 2026-10-26T16:25:04Z: a função PostgreSQL `neondb_owner` na branch principal do Neon `anthares-ara-ha` recebeu uma atualização (`updated_at`). Uma operação `apply_config` foi registrada no mesmo instante.
- A partir de 16:25 UTC os deployments Vercel primário, secundário e de reserva passaram a registrar PostgreSQL `28P01 password authentication failed for user 'neondb_owner'`. Os `DATABASE_URL` dos deployments estavam desatualizados.
- O supervisor Windows registrou `BOTH_HTTP_UNAVAILABLE` e o agente reiniciou repetidamente após HTTP 500 do controlador.
- O Worker Cloudflare armazenava `oauth_owner_callback` via `/v1/mcp/oauth/consume`. Erros HTTP/rede retornavam `false` em `consumeViaControl`, que o callback apresentava incorretamente como `owner_callback_replayed` (409).
- O domínio canônico da reserva também apontava para um deployment anterior após o deploy de correção. O alias precisou ser atualizado. Isso revelou deriva independente de roteamento.

O registro da função e as operações confirmam a alteração no Neon e seu horário. A identidade de quem iniciou a alteração requer auditoria de acesso externa; a atribuição pessoal não foi estabelecida.

## Correções executadas

1. Atualização das credenciais `DATABASE_URL` do primário e secundário e publicação dos deployments; aceitação autenticada `healthy_endpoints: 2`.
2. Criação de `ara_mcp_reserve_runtime`, identidade de banco com senha independente, separada de `neondb_owner`. Foram concedidos `USAGE,CREATE` no schema `public`, `SELECT,INSERT,UPDATE,DELETE` somente nas seis tabelas operacionais `ara_*` existentes e privilégios operacionais nas sequências `ara_*`. Não se concedeu participação na função proprietária `neondb_owner`.
3. Atualização de `DATABASE_URL` do projeto `anthares-ara-vercel-reserve` para a função independente; deploy `dpl_FmurJGjaAQTfrKAQnEFGFS76TKh3` testado com `/healthz=200` e rotas protegidas `/v1/mcp/status` e `/v1/mcp/oauth/consume` retornando 401 sem assinatura. Alias canônico associado à versão aprovada.
4. Worker passou a ter dois destinos Vercel fixos: domínio canônico e alias do projeto. Requisições 404, 429 ou 5xx do primeiro destino autorizam nova tentativa assinada no segundo. Respostas 401, 403 e 409 permanecem terminantes. Idempotência das solicitações `execute` continua a ser preservada pelo corpo original. O segundo alias protege falhas de apontamento, embora ambos compartilhem o mesmo deployment e banco.
5. Callback OAuth retorna `owner_control_unavailable` (503) quando o registro do uso único fica indisponível. Retorna `owner_callback_replayed` (409) apenas diante de registro confirmado de duplicidade. A verificação de uso único e a identidade GitHub foram mantidas.
6. CI testa `owner-github-auth.test.mjs`, sintaxe e integração antes de publicar o Worker. PR [#1454](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1454) aprovado pela suíte e integrado. Deploy de produção efetuado pelo GitHub Actions.

## Duplo monitoramento

- Externo: workflow `.github/workflows/ara-auth-continuity-monitor.yml`, disparo cron a cada 10 minutos, além de execução manual. Verifica Cloudflare MCP, duas URLs da reserva, Vercel primário e secundário. Registra relatório; abre issue GitHub em caso de falha e encerra quando a saúde é restaurada. O GitHub pode atrasar cron em períodos de carga; o intervalo é programado, sem garantia de execução no minuto exato.
- Local: tarefa `Anthares ARA OAuth Continuity Guard` no Windows, a cada 5 minutos, executada como SYSTEM, independente da autenticação do plugin. Script: `C:\ProgramData\AntharesRemoteAgent\ara-auth-continuity-guard.ps1`. Testa o agente e os endpoints, e executa também a prova autenticada `probe-vercel-control.ps1`, que detecta credenciais de primário/ secundário inválidas mesmo quando `/health` retorna 200. Em transições de estado cria eventos Windows 910 (recuperação) e 911 (incidente). Arquivos de estado/log: `ara-auth-continuity-guard-last.json` e `ara-auth-continuity-guard.jsonl`, com rotação por tamanho.
- A rotina de QA completo a cada 12 horas permanece separada destes testes rápidos de disponibilidade.

## Critérios de aceitação

- `https://anthares-ara-mcp.anthares1.workers.dev/` responde 200, `ok=true`, `control_ready=true`, `oauth=true` e `device_connected=true` quando o desktop está conectado.
- Ambas as URLs da reserva respondem 200 em `/healthz`, com `ok=true` e `database=neon`.
- `probe-vercel-control.ps1` registra `healthy_endpoints=2` com chamadas autenticadas de leitura.
- A tarefa Windows termina com `LastTaskResult=0`.
- A suíte OAuth verifica failover quando o destino canônico retorna 503 e impede que a falha simultânea seja classificada como replay. Confirma que uma tentativa posterior continua possível e que o replay real retorna 409.
- Nenhuma chave, URL de banco com senha ou código OAuth deve ser gravado em issue/log de monitoramento.
- O teste de reconexão completa do proprietário requer uma autenticação GitHub iniciada pelo próprio proprietário no ChatGPT. Não é simulado em produção.

## Recuperação segura

1. Consulte o relatório externo e o `ara-auth-continuity-guard-last.json`; diferencie falha de alias, senha, processo local e serviço OAuth.
2. Em falha de banco: compare `updated_at` da função Neon e os erros `28P01` nos logs Vercel. Faça reconciliação da credencial por canal seguro e aplique `DATABASE_URL` no projeto afetado. Nunca imprima credenciais em terminal compartilhado, logs, issues ou documentação.
3. Redeploy do código aprovado sem alterar a base de dados. Prove `/healthz=200` no endereço do novo deployment antes de associar o alias. Confirme posteriormente o alias canônico e o alternativo.
4. Em erro 409 real, exija nova transação OAuth; códigos e nonces são de uso único. Em erro 503 de backend, preserve as regras de replay e recupere conectividade antes de nova autorização.
5. Durante indisponibilidade Vercel/Neon, use os canais independentes WinRemote, MeshCentral e filas privadas GitHub/GitLab do agente para diagnóstico; não execute job remoto duplicado sem idempotência.
6. Na rotação programada de senhas, atualize e valide cada consumidor antes de revogar a credencial antiga. Credenciais independentes da reserva e de `neondb_owner` devem ter ciclos de rotação distintos.
7. Para alterações do Worker, use o CI de `ara-mcp-vercel-primary-deploy.yml`, serializado com o deploy de Claude MCP e protegido com `--keep-vars`.

## Limites expressos

A redundância de aliases não fornece redundância física de banco ou de projeto; ambos são endereços do mesmo projeto Vercel. A conta separada `ara_mcp_reserve_runtime` protege o controlador de reserva contra a rotação isolada de `neondb_owner`. Falha total do Neon, Cloudflare, Vercel ou GitHub, indisponibilidade simultânea de infraestrutura e incidentes de segurança ainda exigem recuperação controlada. Nenhuma arquitetura oferece garantia absoluta de que uma nova indisponibilidade nunca ocorrerá.
