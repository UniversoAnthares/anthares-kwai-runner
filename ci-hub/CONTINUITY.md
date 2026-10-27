# Continuidade operacional Anthares

Atualizado: 2026-10-15T14:25Z.

Este arquivo Ã© normativo para qualquer agente/chat que trabalhe na infraestrutura Anthares. Antes de modificar, testar, migrar ou diagnosticar qualquer componente, o agente deve ler `ci-hub/executor-routing.json`, `ci-hub/provider-status.json`, `test-hub/README.md` e os findings recentes da Ã¡rea.

## Fontes de continuidade obrigatÃ³rias

Antes de decidir ou executar a prÃ³xima fase, o agente deve tambÃ©m reconstruir a fundo o estado dos chats **`SISTEMA DE UPLOADS`** e **`Continuar resoluÃ§Ã£o pendÃªncias`**. DecisÃµes e implementaÃ§Ãµes mais recentes nesses chats prevalecem sobre texto histÃ³rico de fases. Quando houver conflito, adaptar a fase e deixar a alteraÃ§Ã£o registrada em finding/continuidade para os prÃ³ximos agentes.

Regra de precedÃªncia: **instruÃ§Ã£o mais recente e comprovada > implementaÃ§Ã£o real atual > descriÃ§Ã£o histÃ³rica de fase > hipÃ³tese antiga de agente**. A antiga intenÃ§Ã£o de aposentar o MEmu ao chegar Ã  fase F21 foi superada: `MEmu_4` permanece componente gerenciado de standby/bootstrap, iniciando sem janela interativa visÃ­vel e com Ã¡udio desativado, atÃ© nova decisÃ£o explÃ­cita do proprietÃ¡rio.

## SuperfÃ­cies exclusivas

- Controle remoto: **somente Anthares Remote**. NÃ£o usar WinRemote, MeshCentral, Remote Desktop Commander ou outro remote como fallback. Se Anthares Remote falhar, diagnosticar e reparar Anthares Remote.
- AutomaÃ§Ã£o de navegador: **somente Anthares Browser**. Browserless foi substituÃ­do e nÃ£o Ã© fallback. TinyFish tambÃ©m nÃ£o Ã© fallback.
- Render, TinyFish e CircleCI estÃ£o aposentados. Nenhuma funÃ§Ã£o nova pode ser roteada para eles. ReferÃªncias histÃ³ricas podem permanecer em documentaÃ§Ã£o/findings, porÃ©m ficam fora de defaults, prioridades, keepalive, probes e execuÃ§Ã£o.

## Arquitetura Android/Kwai canÃ´nica

A prioridade vigente Ã© obrigatÃ³ria:

1. `physical_android`: celular Android fÃ­sico, executor principal do Kwai.
2. `memu_android`: `MEmu_4`, reserva automÃ¡tica acionÃ¡vel apÃ³s falha comprovada do fÃ­sico e tentativa de recuperaÃ§Ã£o do transporte.
3. `github_android_experimental`: Android/KVM remoto preservado somente para experimento explicitamente autorizado. Ele Ã© inelegÃ­vel para publicaÃ§Ã£o normal e nÃ£o participa do failover automÃ¡tico.

O **Anthares Android Runtime** Ã© a camada de comunicaÃ§Ã£o, supervisÃ£o, recuperaÃ§Ã£o e execuÃ§Ã£o sobre os dispositivos existentes. ADB pode continuar como transporte interno. Detalhes como binÃ¡rio ADB, serial, porta encaminhada e lifecycle do MEmu pertencem ao runtime, e os consumidores devem chamar o runtime.

Falha de transporte e falha do executor sÃ£o estados distintos. Exemplo observado em 2026-10-15: `MEmu_4` com VM `running`, `MEmuHeadless.exe` ativo, porta `127.0.0.1:21543` em listening e transporte ADB `offline`. ClassificaÃ§Ã£o: `BACKEND_RUNNING_TRANSPORT_OFFLINE`.

Antes de trocar de executor, tentar recuperaÃ§Ã£o do transporte do executor atual. Estados de publicaÃ§Ã£o `STARTED`, `COMMITTING` ou `UNCERTAIN` bloqueiam failover. O ledger/fila central, lease e deduplicaÃ§Ã£o continuam autoridades; um resultado incerto nunca autoriza nova publicaÃ§Ã£o por outro executor.

O workflow `.github/workflows/kwai-queue-publisher-v17.yml` foi demovido em 2026-10-15 para experimento explÃ­cito. Ele nÃ£o possui mais gatilho por `push` e exige confirmaÃ§Ã£o manual `EXPERIMENTAL`. O cÃ³digo foi preservado.

## ClassificaÃ§Ã£o antes de agir

Todo problema deve ser classificado antes da correÃ§Ã£o:

1. `ANTHARES_COMPONENT_FAILURE`: falha em Remote, Browser, Reserva, Cloudflare/control-plane ou outro componente Anthares. AÃ§Ã£o: reparar o componente.
2. `PROVIDER_QUOTA`: execuÃ§Ã£o externa bloqueada por quota comprovada. AÃ§Ã£o: marcar o domÃ­nio de quota como inelegÃ­vel e migrar a funÃ§Ã£o para um provedor elegÃ­vel jÃ¡ verificado.
3. `PROVIDER_OUTAGE`: provedor elegÃ­vel indisponÃ­vel sem evidÃªncia de quota. AÃ§Ã£o: failover somente apÃ³s verificar lease/checkpoint e destino elegÃ­vel.
4. `AUTH_OR_SECURITY_BOUNDARY`: MFA, captcha, autorizaÃ§Ã£o de conta ou consentimento irreduzÃ­vel. AÃ§Ã£o: tentar caminhos seguros jÃ¡ implementados; se nÃ£o houver, solicitar a aÃ§Ã£o manual mÃ­nima ao proprietÃ¡rio.
5. `IMPLEMENTATION_GAP`: falta de cÃ³digo/integraÃ§Ã£o. AÃ§Ã£o: implementar diretamente; usar Codex, Kilo ou Work apenas quando isso materialmente ampliar a capacidade.
6. `RETIRED_PROVIDER_REFERENCE`: dependÃªncia ainda aponta para Render, TinyFish, CircleCI ou Browserless. AÃ§Ã£o: migraÃ§Ã£o permanente.

## VerificaÃ§Ã£o de regressÃ£o obrigatÃ³ria por rodada

No inÃ­cio de **cada nova rodada** de trabalho, antes de novas mutaÃ§Ãµes:

1. Reconciliar `SISTEMA DE UPLOADS` + `Continuar resoluÃ§Ã£o pendÃªncias` com o estado real do repositÃ³rio/runtime e identificar decisÃµes superadas.
2. Anthares Remote: `session_status` deve mostrar heartbeat recente e, quando a rodada depender de execuÃ§Ã£o remota, deve haver um `remote_exec` simples bem-sucedido.
3. Roteamento: confirmar Remote exclusivo, Browser exclusivo, `physical_android -> memu_android` para Kwai e provedores aposentados inelegÃ­veis.
4. Provedor usado na rodada: verificar quota/saÃºde mais recente do domÃ­nio especÃ­fico; nÃ£o reutilizar status histÃ³rico como atual.
5. Fluxos jÃ¡ fechados relevantes: revalidar ao menos o sinal de saÃºde que prova ausÃªncia de regressÃ£o.
6. Se uma regressÃ£o aparecer, corrigir a regressÃ£o antes de avanÃ§ar na nova fase, salvo camada independente explicitamente documentada.
7. Atualizar `ci-hub/provider-status.json` quando houver evidÃªncia nova que altere elegibilidade, quota, estado operacional ou data da Ãºltima verificaÃ§Ã£o.

## Quotas sÃ£o domÃ­nios separados

Nunca tratar â€œCloudflareâ€, â€œGitHubâ€ ou â€œGitLabâ€ como uma Ãºnica cota.

- GitHub: Actions pÃºblico e Actions privado sÃ£o domÃ­nios operacionais distintos para seleÃ§Ã£o de executor. Quota privada esgotada nÃ£o bloqueia automaticamente runner pÃºblico.
- Cloudflare: Workers runtime, Workers Builds, Durable Objects/KV e Browser Rendering devem ser verificados separadamente.
- GitLab: `ci_quota_exceeded` bloqueia CI hospedado, preservando leitura/escrita de repositÃ³rio via API/conector.
- Northflank: serviÃ§o operacional nÃ£o prova saldo de cota restante; verificar saldo/limites antes de aumentar capacidade.

## Ordem de decisÃ£o para execuÃ§Ã£o

1. Manter funÃ§Ã£o dentro de Anthares quando a falha for do prÃ³prio sistema.
2. Para Kwai Android, recuperar primeiro o transporte do celular fÃ­sico; depois, se a falha persistir e o estado de publicaÃ§Ã£o permitir, usar MEmu_4.
3. Android/KVM remoto do GitHub permanece fora do failover automÃ¡tico e serve apenas a experimentos explÃ­citos.
4. Para CI finito, preferir GitHub Actions pÃºblico enquanto estiver comprovadamente disponÃ­vel; GitHub privado e GitLab CI ficam fora enquanto `BLOCKED_QUOTA`.
5. Para container/browser persistente, usar Northflank somente apÃ³s verificar estado e limites; a superfÃ­cie continua sendo Anthares Browser.
6. Cloudflare continua elegÃ­vel por domÃ­nio de quota: control-plane/runtime e estado persistente podem operar mesmo se Browser Rendering estiver bloqueado.
7. Codex/Kilo/Work sÃ£o recursos de implementaÃ§Ã£o, nÃ£o provedores de runtime nem remotes.
8. AÃ§Ã£o manual do proprietÃ¡rio Ã© Ãºltimo recurso e deve ser reduzida ao menor passo irreduzÃ­vel.

## Lista fixa â€” adaptaÃ§Ã£o vigente

- F14/F16: concluÃ­das conforme findings e testes registrados.
- F15: mantida para o fim.
- **F17 continua aberta:** provar sessÃ£o Kwai autenticada do alvo exato `@lucasrosalem`, persistente apÃ³s reinÃ­cio, sem publicar conteÃºdo.
- F18â€“F20: somente depois da prova de F17.
- F21 histÃ³rico (â€œaposentar MEmuâ€) estÃ¡ **SUPERSEDED**. Estado vigente: preservar `MEmu_4` como standby/bootstrap gerenciado; autostart, invisÃ­vel/nÃ£o interativo e mudo.
- EvidÃªncia TikTok nÃ£o fecha F17.

## Estado desta rodada

- Anthares Remote: conectado e executando comandos. Houve pelo menos um `execution_outcome_unknown`; mutaÃ§Ãµes posteriores foram conduzidas por detached jobs e verificadas por estado/log para evitar repetiÃ§Ã£o cega.
- Celular fÃ­sico canÃ´nico `993fce720408`: ausente de `adb devices` durante a validaÃ§Ã£o de 2026-10-15; recuperaÃ§Ã£o de transporte foi tentada e esgotada.
- `MEmu_4`: reinstaurado headless como reserva; VM observada `running`; `MEmuHeadless.exe` ativo; Ã¡udio `none`; ADB forwarding atual `127.0.0.1:21543 -> 10.0.2.15:5555`.
- Transporte MEmu atual: `offline` mesmo apÃ³s start-server, disconnect/connect, polling, reinÃ­cio controlado do backend e novo start headless. O backend permanece preservado e nenhuma limpeza de dados/reinstalaÃ§Ã£o do Kwai foi realizada.
- Teste de seguranÃ§a `PublicationState=UNCERTAIN`: seleÃ§Ã£o retornou `selected=null` e bloqueou failover, comprovando a barreira contra duplicaÃ§Ã£o no runtime.
- Nenhuma publicaÃ§Ã£o Kwai foi executada nesta rodada.
- F17 permanece aberta enquanto o transporte MEmu estiver indisponÃ­vel e o celular fÃ­sico estiver ausente.
- GitLab CI: bloqueado por `ci_quota_exceeded`, conforme pipeline 2947796926.
- GitHub Actions pÃºblico: Ãºltimo runner comprovado em 2026-10-15; seu Android virtual fica fora do caminho normal de publicaÃ§Ã£o Kwai.
- Cloudflare control/vault: Ãºltimo sinal operacional HTTP 200; Browser Rendering segue inelegÃ­vel enquanto o bloqueio 429 nÃ£o for superado.
- Northflank: serviÃ§os previamente operacionais; saldo de quota continua exigindo verificaÃ§Ã£o antes de nova capacidade.

Finding detalhado desta correÃ§Ã£o: `test-hub/findings/20261015-android-runtime-physical-first-correction.md`.

## Android Runtime authority rule â€” 2026-10-16

For `MEmu_4`, there is exactly one recovery authority: **Anthares Android Runtime running from the SYSTEM path**. The direct SYSTEM/headless path is primary. The interactive `Lucas` launcher and isolated ADB helper are redundancy-only and must remain disabled outside an explicit fallback attempt. They must never run as a parallel watchdog or alternate authority. The runtime serializes MEmu recovery with the global recovery mutex and may invoke the interactive redundancy only after the SYSTEM path exhausts its bounded recovery window. Do not promote the interactive path to primary without a new explicit owner decision.

## 2026-10-26 — Bitrise e AppVeyor (decisao operacional atual)

A fila geral de CI do `ci-hub/executor-routing.json` preserva AppVeyor como **penultimo candidato** antes de GitLab CI. O AppVeyor permanece registrado, mas foi marcado como inelegivel para novos jobs apos resposta HTTP 500 em POST /api/builds com API key v1 autenticada e historico sem novo build. Antes de dispatch, erros confirmados autorizam considerar o proximo provedor que tenha readiness e quota atual; timeouts ou efeitos ambiguos exigem reconciliacao do job antes de nova tentativa, com fencing e deduplicacao. Esta regra nao autoriza repetir publicacao.

Bitrise permanece candidato **desativado** ate autenticar a conta, confirmar creditos Hobby gratuitos, trocar no projeto remoto a origem da configuracao de "Stored on Bitrise" para o `bitrise.yml` versionado e validar o workflow `anthares_ci_smoke`. Ele nao publica, nao executa AVD nem instala apps. O workflow `primary` foi preservado integralmente para futura homologacao especifica de Android e browser.

**Limite de evidencia:** a configuracao no repositório e os testes locais nao comprovam acesso a conta Bitrise, configuracao ativa no serviço nem execucao hospedada. Nao promover Bitrise a `ci_eligible=true` ou `active=true` sem links e logs de um job real. A prioridade CI e um manifesto de decisao; selecao/configuracao nao garante dispatch automatico entre provedores.

