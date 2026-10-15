# Continuidade operacional Anthares

Atualizado: 2026-10-15T14:25Z.

Este arquivo é normativo para qualquer agente/chat que trabalhe na infraestrutura Anthares. Antes de modificar, testar, migrar ou diagnosticar qualquer componente, o agente deve ler `ci-hub/executor-routing.json`, `ci-hub/provider-status.json`, `test-hub/README.md` e os findings recentes da área.

## Fontes de continuidade obrigatórias

Antes de decidir ou executar a próxima fase, o agente deve também reconstruir a fundo o estado dos chats **`SISTEMA DE UPLOADS`** e **`Continuar resolução pendências`**. Decisões e implementações mais recentes nesses chats prevalecem sobre texto histórico de fases. Quando houver conflito, adaptar a fase e deixar a alteração registrada em finding/continuidade para os próximos agentes.

Regra de precedência: **instrução mais recente e comprovada > implementação real atual > descrição histórica de fase > hipótese antiga de agente**. A antiga intenção de aposentar o MEmu ao chegar à fase F21 foi superada: `MEmu_4` permanece componente gerenciado de standby/bootstrap, iniciando sem janela interativa visível e com áudio desativado, até nova decisão explícita do proprietário.

## Superfícies exclusivas

- Controle remoto: **somente Anthares Remote**. Não usar WinRemote, MeshCentral, Remote Desktop Commander ou outro remote como fallback. Se Anthares Remote falhar, diagnosticar e reparar Anthares Remote.
- Automação de navegador: **somente Anthares Browser**. Browserless foi substituído e não é fallback. TinyFish também não é fallback.
- Render, TinyFish e CircleCI estão aposentados. Nenhuma função nova pode ser roteada para eles. Referências históricas podem permanecer em documentação/findings, porém ficam fora de defaults, prioridades, keepalive, probes e execução.

## Arquitetura Android/Kwai canônica

A prioridade vigente é obrigatória:

1. `physical_android`: celular Android físico, executor principal do Kwai.
2. `memu_android`: `MEmu_4`, reserva automática acionável após falha comprovada do físico e tentativa de recuperação do transporte.
3. `github_android_experimental`: Android/KVM remoto preservado somente para experimento explicitamente autorizado. Ele é inelegível para publicação normal e não participa do failover automático.

O **Anthares Android Runtime** é a camada de comunicação, supervisão, recuperação e execução sobre os dispositivos existentes. ADB pode continuar como transporte interno. Detalhes como binário ADB, serial, porta encaminhada e lifecycle do MEmu pertencem ao runtime, e os consumidores devem chamar o runtime.

Falha de transporte e falha do executor são estados distintos. Exemplo observado em 2026-10-15: `MEmu_4` com VM `running`, `MEmuHeadless.exe` ativo, porta `127.0.0.1:21543` em listening e transporte ADB `offline`. Classificação: `BACKEND_RUNNING_TRANSPORT_OFFLINE`.

Antes de trocar de executor, tentar recuperação do transporte do executor atual. Estados de publicação `STARTED`, `COMMITTING` ou `UNCERTAIN` bloqueiam failover. O ledger/fila central, lease e deduplicação continuam autoridades; um resultado incerto nunca autoriza nova publicação por outro executor.

O workflow `.github/workflows/kwai-queue-publisher-v17.yml` foi demovido em 2026-10-15 para experimento explícito. Ele não possui mais gatilho por `push` e exige confirmação manual `EXPERIMENTAL`. O código foi preservado.

## Classificação antes de agir

Todo problema deve ser classificado antes da correção:

1. `ANTHARES_COMPONENT_FAILURE`: falha em Remote, Browser, Reserva, Cloudflare/control-plane ou outro componente Anthares. Ação: reparar o componente.
2. `PROVIDER_QUOTA`: execução externa bloqueada por quota comprovada. Ação: marcar o domínio de quota como inelegível e migrar a função para um provedor elegível já verificado.
3. `PROVIDER_OUTAGE`: provedor elegível indisponível sem evidência de quota. Ação: failover somente após verificar lease/checkpoint e destino elegível.
4. `AUTH_OR_SECURITY_BOUNDARY`: MFA, captcha, autorização de conta ou consentimento irreduzível. Ação: tentar caminhos seguros já implementados; se não houver, solicitar a ação manual mínima ao proprietário.
5. `IMPLEMENTATION_GAP`: falta de código/integração. Ação: implementar diretamente; usar Codex, Kilo ou Work apenas quando isso materialmente ampliar a capacidade.
6. `RETIRED_PROVIDER_REFERENCE`: dependência ainda aponta para Render, TinyFish, CircleCI ou Browserless. Ação: migração permanente.

## Verificação de regressão obrigatória por rodada

No início de **cada nova rodada** de trabalho, antes de novas mutações:

1. Reconciliar `SISTEMA DE UPLOADS` + `Continuar resolução pendências` com o estado real do repositório/runtime e identificar decisões superadas.
2. Anthares Remote: `session_status` deve mostrar heartbeat recente e, quando a rodada depender de execução remota, deve haver um `remote_exec` simples bem-sucedido.
3. Roteamento: confirmar Remote exclusivo, Browser exclusivo, `physical_android -> memu_android` para Kwai e provedores aposentados inelegíveis.
4. Provedor usado na rodada: verificar quota/saúde mais recente do domínio específico; não reutilizar status histórico como atual.
5. Fluxos já fechados relevantes: revalidar ao menos o sinal de saúde que prova ausência de regressão.
6. Se uma regressão aparecer, corrigir a regressão antes de avançar na nova fase, salvo camada independente explicitamente documentada.
7. Atualizar `ci-hub/provider-status.json` quando houver evidência nova que altere elegibilidade, quota, estado operacional ou data da última verificação.

## Quotas são domínios separados

Nunca tratar “Cloudflare”, “GitHub” ou “GitLab” como uma única cota.

- GitHub: Actions público e Actions privado são domínios operacionais distintos para seleção de executor. Quota privada esgotada não bloqueia automaticamente runner público.
- Cloudflare: Workers runtime, Workers Builds, Durable Objects/KV e Browser Rendering devem ser verificados separadamente.
- GitLab: `ci_quota_exceeded` bloqueia CI hospedado, preservando leitura/escrita de repositório via API/conector.
- Northflank: serviço operacional não prova saldo de cota restante; verificar saldo/limites antes de aumentar capacidade.

## Ordem de decisão para execução

1. Manter função dentro de Anthares quando a falha for do próprio sistema.
2. Para Kwai Android, recuperar primeiro o transporte do celular físico; depois, se a falha persistir e o estado de publicação permitir, usar MEmu_4.
3. Android/KVM remoto do GitHub permanece fora do failover automático e serve apenas a experimentos explícitos.
4. Para CI finito, preferir GitHub Actions público enquanto estiver comprovadamente disponível; GitHub privado e GitLab CI ficam fora enquanto `BLOCKED_QUOTA`.
5. Para container/browser persistente, usar Northflank somente após verificar estado e limites; a superfície continua sendo Anthares Browser.
6. Cloudflare continua elegível por domínio de quota: control-plane/runtime e estado persistente podem operar mesmo se Browser Rendering estiver bloqueado.
7. Codex/Kilo/Work são recursos de implementação, não provedores de runtime nem remotes.
8. Ação manual do proprietário é último recurso e deve ser reduzida ao menor passo irreduzível.

## Lista fixa — adaptação vigente

- F14/F16: concluídas conforme findings e testes registrados.
- F15: mantida para o fim.
- **F17 continua aberta:** provar sessão Kwai autenticada do alvo exato `@lucasrosalem`, persistente após reinício, sem publicar conteúdo.
- F18–F20: somente depois da prova de F17.
- F21 histórico (“aposentar MEmu”) está **SUPERSEDED**. Estado vigente: preservar `MEmu_4` como standby/bootstrap gerenciado; autostart, invisível/não interativo e mudo.
- Evidência TikTok não fecha F17.

## Estado desta rodada

- Anthares Remote: conectado e executando comandos. Houve pelo menos um `execution_outcome_unknown`; mutações posteriores foram conduzidas por detached jobs e verificadas por estado/log para evitar repetição cega.
- Celular físico canônico `993fce720408`: ausente de `adb devices` durante a validação de 2026-10-15; recuperação de transporte foi tentada e esgotada.
- `MEmu_4`: reinstaurado headless como reserva; VM observada `running`; `MEmuHeadless.exe` ativo; áudio `none`; ADB forwarding atual `127.0.0.1:21543 -> 10.0.2.15:5555`.
- Transporte MEmu atual: `offline` mesmo após start-server, disconnect/connect, polling, reinício controlado do backend e novo start headless. O backend permanece preservado e nenhuma limpeza de dados/reinstalação do Kwai foi realizada.
- Teste de segurança `PublicationState=UNCERTAIN`: seleção retornou `selected=null` e bloqueou failover, comprovando a barreira contra duplicação no runtime.
- Nenhuma publicação Kwai foi executada nesta rodada.
- F17 permanece aberta enquanto o transporte MEmu estiver indisponível e o celular físico estiver ausente.
- GitLab CI: bloqueado por `ci_quota_exceeded`, conforme pipeline 2947796926.
- GitHub Actions público: último runner comprovado em 2026-10-15; seu Android virtual fica fora do caminho normal de publicação Kwai.
- Cloudflare control/vault: último sinal operacional HTTP 200; Browser Rendering segue inelegível enquanto o bloqueio 429 não for superado.
- Northflank: serviços previamente operacionais; saldo de quota continua exigindo verificação antes de nova capacidade.

Finding detalhado desta correção: `test-hub/findings/20261015-android-runtime-physical-first-correction.md`.
