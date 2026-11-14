# Handoff AGENTE 02 → AGENTE 03 — SpawnDroid Kwai (2026-11-14)

## Status e evidência
- Branch: `agent02/spawndroid-webdriver-proof-20261114`; PR #2609.
- Workflow Hub: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43596034043 (10/10 testes offline; remote-canary **skipped**).
- Preflight: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43596034080 (offline; sem dispositivo).
- **Nenhuma sessão Android real foi iniciada por este agente.** ID Android, ARM64, consumo, término no SpawnDroid e aplicativo em execução real: PENDENTES.
- Publicação, login e cutover continuam desabilitados.

## Pré-requisitos obrigatórios antes de iniciar
1. O AGENTE 01 precisa registrar no workspace correto o APK original verificado, pacote `com.kwai.video`, e compartilhar identificador `app.slug` **sem** compartilhar arquivos nem credenciais em logs.
2. Confirmar no console SpawnDroid autenticado: usuário, workspace/organização, Hobby gratuito, saldo de minutos do mês, cota sem excedente, slot disponível (1 runner), limite de 15 minutos, timeout ocioso e ausência de sessão RUNNING/READY.
3. Secrets GitHub Actions: `SPAWNDROID_CI_TOKEN` do Hub e, para inspeções independentes, `SPAWNDROID_API_KEY` com escopo de leitura (os valores nunca devem aparecer no log).
4. Verificar ausência de outra execução do workflow `kwai-spawndroid-hub.yml` ou `kwai-spawndroid-preflight.yml` concorrente. Ambos usam agora o grupo `kwai-spawndroid-experimental`.
5. Registrar antes da criação: owner=AGENTE02/03, sessão pendente, GitHub run ID, horário, deadline máximo <= 180 s no canário, plano de cancelamento e reconciliação do caso POST incerto.

## Procedimento previsto — apenas depois dos gates
1. Executar preflight `kwai-spawndroid-preflight.yml` modo `status` (consulta apps/perfis; nenhuma sessão).
2. Executar manualmente `kwai-spawndroid-hub.yml`, `canary=true`, `artifact_slug=<slug validado>`. Exige `SPAWNDROID_HOBBY_FREE_CONFIRMED=1` atual e `SPAWNDROID_CI_TOKEN`.
3. No Hub WebDriver o adaptador efetua `POST /session` com Appium 3/UiAutomator2, `spawndroid:app=<slug>`, `spawndroid:profile=android-14-phone`. Obtém ID W3C, capabilities com `appium:udid` e `platformVersion`, verifica `spawndroid:appPackage=com.kwai.video`.
4. Aciona `mobile: activateApp`; consulta `mobile: queryAppState` exigindo 4 (foreground); lê `GET /session/:id/source` exigindo árvore de UI Android.
5. Em `finally`, envia `DELETE /session/:id?result=passed|failed` e verifica `GET /session/:id` com 404. Essa prova confirma **apenas** o encerramento da sessão W3C.
6. Consultar separadamente o painel Runs/API de SpawnDroid e conferir estado terminal da **reserva/dispositivo** original, registro de tempo consumido, minutos restantes, device info/ABI ARM64, logs e ausência de sessão ativa. Se houver dúvida, registrar `CANCEL_UNCONFIRMED` e bloquear qualquer novo lançamento.
7. O canário atual encerra com código 22 depois da prova W3C, deliberadamente, até que a verificação de encerramento do dispositivo no provedor seja implementada e validada. Não interpretar falha 22 como falha do aplicativo.
8. Uma vez homologado, criar finding Test Hub com IDs reais, horários, logs sanitizados e aprovação do encerramento. Esse experimento **não** autoriza login, vídeo, Neon, publicadores nem mudança de `cloud_cutover.enabled`.

## Limites
O controle é lançado no runner GitHub-hosted, separado do PC pessoal. Prova de execução realmente remota e ARM64 requer uma sessão real e leitura do provedor. O slot Hobby é efêmero e perde dados de aplicativos ao fechar. Não promover como Android persistente em produção.
