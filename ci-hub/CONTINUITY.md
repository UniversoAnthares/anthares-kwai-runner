# Continuidade operacional Anthares

Atualizado: 2026-10-15T05:30Z.

Este arquivo é normativo para qualquer agente/chat que trabalhe na infraestrutura Anthares. Antes de modificar, testar, migrar ou diagnosticar qualquer componente, o agente deve ler `ci-hub/executor-routing.json`, `ci-hub/provider-status.json`, `test-hub/README.md` e os findings recentes da área.

## Fontes de continuidade obrigatórias

Antes de decidir ou executar a próxima fase, o agente deve também reconstruir a fundo o estado dos chats **`SISTEMA DE UPLOADS`** e **`ITENS FIXOS, TOTAIS`**. Não basta reutilizar uma conclusão antiga da lista fixa: decisões e implementações mais recentes nesses dois chats prevalecem sobre texto histórico de fases. Quando houver conflito, adaptar a fase e deixar a alteração registrada em finding/continuidade para os próximos agentes.

Regra de precedência: **instrução mais recente e comprovada > descrição histórica de fase > hipótese antiga de agente**. Em particular, a antiga intenção de aposentar o MEmu ao chegar à fase F21 foi superada: `MEmu_4` deve permanecer como componente gerenciado de standby/bootstrap, iniciando com o computador, sem janela interativa visível e com áudio desativado, até nova decisão explícita do proprietário.

## Superfícies exclusivas

- Controle remoto: **somente Anthares Remote**. Não usar WinRemote, MeshCentral, Remote Desktop Commander ou outro remote como fallback. Se Anthares Remote falhar, diagnosticar e reparar Anthares Remote.
- Automação de navegador: **somente Anthares Browser**. Browserless foi substituído e não é fallback. TinyFish também não é fallback.
- Render, TinyFish e CircleCI estão aposentados. Nenhuma função nova pode ser roteada para eles. Referências históricas podem permanecer em documentação/findings, mas não em defaults, prioridades, keepalive, probes ou execução.

## Classificação antes de agir

Todo problema deve ser classificado antes da correção:

1. `ANTHARES_COMPONENT_FAILURE`: falha em Remote, Browser, Reserva, Cloudflare/control-plane ou outro componente Anthares. Ação: reparar o componente; não trocar por ferramenta externa equivalente.
2. `PROVIDER_QUOTA`: execução externa bloqueada por quota comprovada. Ação: marcar o domínio de quota como inelegível e migrar a função para um provedor elegível já verificado.
3. `PROVIDER_OUTAGE`: provedor elegível está indisponível sem evidência de quota. Ação: failover apenas após verificar lease/checkpoint e destino elegível.
4. `AUTH_OR_SECURITY_BOUNDARY`: MFA, captcha, autorização de conta ou consentimento irreduzível. Ação: tentar todos os caminhos seguros já implementados; se não houver, solicitar a ação manual mínima ao proprietário.
5. `IMPLEMENTATION_GAP`: falta de código/integração, não de infraestrutura. Ação: implementar diretamente; usar Codex, Kilo ou Work apenas quando isso materialmente ampliar a capacidade, nunca como substituto automático do Anthares Remote/Browser.
6. `RETIRED_PROVIDER_REFERENCE`: dependência ainda aponta para Render, TinyFish, CircleCI ou Browserless. Ação: migração permanente; nunca reativar o provedor aposentado.

## Verificação de regressão obrigatória por rodada

No início de **cada nova rodada** de trabalho, antes de novas mutações:

1. Reconciliar `SISTEMA DE UPLOADS` + `ITENS FIXOS, TOTAIS` com o estado real do repositório/runtime e identificar decisões superadas.
2. Anthares Remote: `session_status` deve mostrar heartbeat recente e, quando a rodada depender de execução remota, deve haver um `remote_exec` simples bem-sucedido.
3. Roteamento: confirmar que `executor-routing.json` ainda mantém Remote exclusivo e Browser exclusivo e que aposentados continuam inelegíveis.
4. Provedor usado na rodada: verificar quota/saúde mais recente do domínio específico; não reutilizar status histórico como atual.
5. Fluxos já fechados relevantes: revalidar ao menos o sinal de saúde que prova que não regrediram. Ex.: Cloudflare control/vault HTTP 200; Northflank BUILD=SUCCESS/DEPLOY=COMPLETED; CI público aloca runner quando ele for usado.
6. Se uma regressão aparecer, corrigir a regressão antes de avançar na nova fase, salvo se ela estiver em camada independente e documentada como tal.
7. Atualizar `ci-hub/provider-status.json` quando houver evidência nova que altere elegibilidade, quota, estado operacional ou data da última verificação.

## Quotas são domínios separados

Nunca tratar “Cloudflare”, “GitHub” ou “GitLab” como uma única cota.

- GitHub: Actions público e Actions privado são domínios operacionais distintos para seleção de executor. Quota privada esgotada não bloqueia automaticamente runner público.
- Cloudflare: Workers runtime, Workers Builds, Durable Objects/KV e Browser Rendering devem ser verificados separadamente. Browser Rendering 429 não significa que Workers runtime ou Durable Objects estejam indisponíveis.
- GitLab: `ci_quota_exceeded` bloqueia CI hospedado, não leitura/escrita de repositório via GitLab API/conector.
- Northflank: serviço operacional não prova saldo de cota restante; verificar saldo/limites antes de aumentar número de serviços ou capacidade.

## Ordem de decisão para execução

1. Manter função dentro de Anthares quando a falha for do próprio sistema.
2. Se o bloqueio for quota externa, usar o primeiro provedor elegível com verificação fresca e capacidade apropriada.
3. Para CI finito, preferir GitHub Actions público enquanto estiver comprovadamente disponível; não usar GitHub privado ou GitLab CI enquanto estiverem `BLOCKED_QUOTA`.
4. Para container/browser persistente, usar Northflank somente após verificar estado e limites; a superfície continua sendo Anthares Browser, não Northflank diretamente para o usuário/agente.
5. Cloudflare continua elegível por domínio de quota: control-plane/runtime e estado persistente podem continuar mesmo se Browser Rendering estiver bloqueado.
6. Codex/Kilo/Work são recursos de implementação, não provedores de runtime nem remotes.
7. Ação manual do proprietário é último recurso e deve ser reduzida ao menor passo irreduzível.

## Lista fixa — adaptação vigente

- F14/F16: concluídas conforme findings e testes já registrados.
- F15: mantida para o fim, conforme decisão vigente da lista fixa.
- **F17 é a pendência corrente:** provar sessão Kwai autenticada do alvo exato `@lucasrosalem`, persistente após reinício, sem publicar conteúdo.
- F18–F20: somente depois da prova de F17.
- F21 histórico (“aposentar MEmu”) está **SUPERSEDED**. Estado vigente: preservar `MEmu_4` como standby/bootstrap gerenciado; autostart no boot, invisível/não interativo e mudo.
- Não fechar F17 usando evidência de TikTok: a prova precisa ser da sessão Kwai e da conta exata.

## Estado desta rodada

- Anthares Remote: verificado conectado e executando comandos nesta rodada; fila sem lease pendente e roundtrip `ARA_ROUNDTRIP_OK`.
- `MEmu_4`: em execução e acessível por ADB em `127.0.0.1:21543`; pacote Kwai presente e foreground observado no app.
- Watchdog local `Anthares-MEmu-Standby-Watchdog`: encontrado, porém ainda apontava historicamente para `MEmu` e gatilho de logon; precisa ser corrigido para `MEmu_4`/boot como parte de F17.
- Áudio de `MEmu_4`: configuração ainda não estava comprovadamente desativada no início desta rodada; faz parte da correção corrente.
- GitLab CI: bloqueado por `ci_quota_exceeded`, verificado no pipeline 2947796926.
- GitHub Actions público: runner alocado e executado em 2026-10-15; não confundir com quota de Actions privado.
- Cloudflare control/vault: último sinal operacional HTTP 200; Browser Rendering continua inelegível enquanto o 429 não for superado pelo caminho interno do Anthares Browser.
- Northflank ARA/TikTok: último estado conhecido build success/deploy completed; saldo de quota não deve ser inferido desse sinal.
