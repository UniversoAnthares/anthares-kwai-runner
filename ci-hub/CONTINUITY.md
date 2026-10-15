# Continuidade operacional Anthares

Atualizado: 2026-10-15T03:10Z.

Este arquivo é normativo para qualquer agente/chat que trabalhe na infraestrutura Anthares. Antes de modificar, testar, migrar ou diagnosticar qualquer componente, o agente deve ler `ci-hub/executor-routing.json`, `ci-hub/provider-status.json`, `test-hub/README.md` e os findings recentes da área.

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

1. Anthares Remote: `session_status` deve mostrar heartbeat recente e, quando a rodada depender de execução remota, deve haver um `remote_exec` simples bem-sucedido.
2. Roteamento: confirmar que `executor-routing.json` ainda mantém Remote exclusivo e Browser exclusivo e que aposentados continuam inelegíveis.
3. Provedor usado na rodada: verificar quota/saúde mais recente do domínio específico; não reutilizar status histórico como atual.
4. Fluxos já fechados relevantes: revalidar ao menos o sinal de saúde que prova que não regrediram. Ex.: Cloudflare control/vault HTTP 200; Northflank BUILD=SUCCESS/DEPLOY=COMPLETED; CI público aloca runner quando ele for usado.
5. Se uma regressão aparecer, corrigir a regressão antes de avançar na nova fase, salvo se ela estiver em camada independente e documentada como tal.
6. Atualizar `ci-hub/provider-status.json` quando houver evidência nova que altere elegibilidade, quota, estado operacional ou data da última verificação.

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

## Estado desta rodada

- Anthares Remote: verificado conectado e executando comandos em 2026-10-15T03:06Z.
- GitLab CI: bloqueado por `ci_quota_exceeded`, verificado no pipeline 2947796926.
- GitHub Actions público: runner alocado e executado em 2026-10-15T03:08Z; a falha observada no watchdog foi lógica/configuração, não quota.
- Cloudflare control e vault: HTTP 200 em 2026-10-15T03:07Z; estado persistente ativo.
- Anthares Reserva Browser: `/health` HTTP 200; binding de browser/estado presente; autenticação real não validada nesta rodada.
- Northflank ARA e TikTok: build success e deploy completed em 2026-10-15T03:09Z.
- GitHub Actions privado: bloqueio de quota informado pelo proprietário; billing API não está disponível neste conector, portanto permanece pendente de verificação direta.
- Cloudflare Browser Rendering: último estado conhecido bloqueado por 429; revalidação deve ocorrer apenas por caminho interno do Anthares Browser quando necessária.
