# Kwai — plano operacional de 13/11/2026: zero custo, sem Oracle, sem PC ou Android físico

STATUS: REVISED_AFTER_REGRESSION_2576. Decisão original relevante: `test-hub/findings/20261005-1741-architecture-decisoes-aceitacao.md`.
NENHUMA PROPOSTA DE PLANO PAGO, TESTE COM CARTÃO, CONTRATAÇÃO, PATROCÍNIO QUE EXIJA ESPERAR RESPOSTA OU EXCEÇÃO FINANCEIRA. Esta regra é definitiva na fase atual e está fixada em `ci-hub/executor-routing.json` (`android_execution.financial_policy`).
Custo incremental autorizado: R$ 0; operações comerciais e duas contas brasileiras: `lucasrosalem` e `universoanthares`. Prazo de publicação diária: entre 06h e 23h, horários calculados proporcionalmente pela fila Neon.

## Caminhos encerrados — reabertura somente por decisão explícita e prova nova
1. **Oracle/Ampere:** titular ordenou parar de verificar e de provisionar. PR #2575 tornou os dois workflows de monitoramento e smoke inertes. O alerta ChatGPT também foi desativado. Não criar nova rotina Oracle em nenhum repositório.
2. **CutMotions:** tentativa de cadastro falhou em 04/10/2026 (`Registration failed`), exigindo organização afiliada/habilitada pelo Kwai. A lista de decisões de 05/10 já excluía esta rota. O PR #2576 sugeriu indevidamente seu retorno; **esse trecho está revogado aqui**. O redirecionamento oficial de `cp.kwai.com` para CutMotions não fornece autorização para as nossas contas.
3. **Kuaishou Open Platform:** API chinesa `user_video_publish` sem compatibilidade/autorização comprovada das contas brasileiras; excluída desde 05/10.
4. **GitHub Actions como Android publicador:** muitos testes falharam para uploads reais autenticados; `github_android_experimental` continua ineligível em produção. GitHub serve apenas como controlador, CI, fila, compilador de relatórios e gatilho de provisionamento **em provedor aprovado**, nunca como promotor de publicações via emulador hospedado.
5. **PC, MEmu e Android físico após a migração:** inadmissíveis como arquitetura final. Preservar o publicador atual somente como transição até a publicação em nuvem comprovada; não interromper a rotina existente prematuramente.
6. **Kwai Studio, portal web antigo, Play Store/Aurora como fonte principal de APKs, túneis/VNC públicos e APKs não confiáveis:** continuam excluídos pelas decisões anteriores.

## Diagnóstico real de viabilidade

O Kwai Brasil não tem interface pública de postagem programática documentada/entregue para estas contas. A alternativa testável exige Android real em kernel Linux com binder (ou um telefone Android remoto hospedado por terceiro) e autenticação do próprio aplicativo.

**Hospedagem comercial e free tiers:** Cloudflare Containers exige Workers Paid e cobra consumo; o Google e2-micro gratuito tem RAM insuficiente; Hostinger shared hosting/Forgejo é executor de CI sem prova de kernel binder e root de host. SpawnDroid Hobby oferece apenas 200 device-minutes mensais, sessões de 15 minutos e encerramento por inatividade; HubSim oferece cloud Android 4 GB a €15/mês (100 créditos iniciais são teste); FreeVPS.org e NanoKVM exigem histórico de participação em comunidades e usualmente oferecem recursos inferiores; FOSSVPS oferece 2 vCPU/4 GiB/64 GiB, porém proíbe uso comercial e exige desenvolvimento FOSS. VPSFree.io publiciza 2–6 GB, mas seu catálogo gratuito efetivamente consultado mostrou 192 MB e 3 GB; Verta Cloud não forneceu contrato/VM verificável e falhou ao abrir o portal. Não usar a existência de homepage como prova de máquina entregue.

**Conclusão de engenharia:** não existe até a data deste documento uma rota externa **homologada** que satisfaça simultaneamente R$0, Android independente de PC/celular, disponibilidade contínua, duas contas Kwai e volume diário de publicações. O código por si só não supre CPU/RAM/kernel. Uma VPS confiável, **gratuita por cessão/patrocínio**, sem proibição comercial e com kernel compatível é a única rota independente que preserva todas as restrições; sua obtenção depende de aceitação externa real. Portanto, a implantação final está BLOQUEADA até existir recurso material comprovado.

## Plano executável, com decisões binárias

### Etapa 1 — Verificar somente infraestrutura gratuita já acessível (BLOQUEADA para migração)
Usar exclusivamente recursos que já existam nas contas conectadas, com custo incremental comprovadamente R$ 0 e disponibilidade imediata: Linux com root real, binder/binderfs, 2 vCPU, 4 GiB RAM, 20 GiB livres e tráfego suficiente. **Não solicitar cadastros, patrocínios, aprovações externas ou contratação.** Serviços existentes de containers podem controlar a fila sem suportar o Android. Sem host qualificado, encerrar esta etapa como BLOQUEADA e prosseguir somente com correções offline da fila. O monitor de catálogos é apenas leitura e não comprova VM entregue.

### Etapa 2 — Pré-teste em VM entregue (CÓDIGO PRONTO)
No novo host aprovado, rodar `tools/redroid_free_vps_preflight.py`. Exigir KVM/VM equivalente com controle de kernel, Docker privilegiado, dispositivos binder reais e capacidade de upload. `CANDIDATE_FOR_ISOLATED_INSTALL_TEST` autoriza apenas o teste isolado, sem senhas Kwai. Se falhar, encerrar esta oferta e preservar a fila, sem gastar.

### Etapa 3 — Instalar Android e homologar apps (CÓDIGO BASE PRONTO)
Usar o cloud-init portável `infra/oci-android/redroid-firstboot.cloud-config.yml` **somente como bootstrap Linux genérico em provedor não Oracle**, mantendo digests fixos para imagens ARM64/AMD64, ADB vinculado a loopback, persistência do armazenamento e health/reboot. Validar `sys.boot_completed=1`, funcionamento Kwai/Kwai Lite, contas corretas e reinicialização sem precisar do PC.

### Etapa 4 — Ligar duas contas à fila Neon e provar postagens (CÓDIGO BASE PRONTO)
Implantar a função `cortesqueue` no projeto Neon efetivamente autorizado, com `kwai-persistent-cloud-identity.mjs` e cliente `tools/kwai_persistent_cloud_queue.py`. A função de produção não estava no escopo do conector Neon disponível em 13/11/2026; obter acesso ao projeto correto é um impedimento próprio. Configurar token exclusivo da VM, impedir tarefas paralelas entre dispositivos, preservar `lease_generation`, reconciliação de publicação incerta, prova independente do post real em cada conta, janelas de 06–23h e idempotência.

### Etapa 5 — Migrar sem perda ou duplicação (AINDA NÃO AUTORIZADA)
Exigir todos os oito comprovantes `android_execution.cloud_cutover.required_proofs`; só então aprovar `cloud_cutover.enabled=true` por alteração revisada. Confirmar ciclo completo com computador e Android físico desligados, persistência após reboot, links públicos nas duas contas e custo zero. Se o executor remoto falhar, deixar tarefas na fila; nunca repostar estado incerto.

## Limite absoluto de zero custo e nenhum tempo aguardando terceiros
O titular proibiu recomendações de qualquer plano pago, teste com cartão, contratação, sugestão de exceção orçamentária e candidaturas que dependam de resposta externa. **Não sugerir novamente** VPS comercial, promoção, trial com forma de pagamento, sponsorship application ou aguardar aprovação. Manter Oracle, CutMotions, Kuaishou e emulador GitHub excluídos.
Apenas executar tarefas possíveis imediatamente em serviços **já conectados e gratuitos**, sem habilitar publicadores experimentais: correções seguras da fila Neon, identidades de conta, pacing até 23h, deduplicação, testes em CI, reconciliação sem repetição e preservação do publicador atual.
O objetivo de publicação integralmente na nuvem, com PC/Android físico desligados, permanece **BLOQUEADO_POR_RECURSO_REAL** enquanto não houver servidor autorizado efetivamente disponível com custo zero. O desenvolvimento de código não equivale a um host em execução, e nunca autoriza simular publicações nem alterar o roteamento.

## Referências diretas
- Evidência de exclusões: `test-hub/findings/20261005-1741-architecture-decisoes-aceitacao.md`.
- Custos oficial Cloudflare: https://developers.cloudflare.com/containers/platform/pricing/
- Sessões do SpawnDroid: https://spawndroid.io/pricing/ e https://spawndroid.io/changelog/
- Host Android pago: https://hubsim.com/
- Critérios da comunidade: https://freevps.org/ e https://fossvps.org/
- Pré-teste: `tools/redroid_free_vps_preflight.py`, `tests/test_redroid_free_vps_preflight.py`.
- Roteamento protegido: `ci-hub/executor-routing.json`, `docs/KWAI-CLOUD-CUTOVER-CONTRACT.md`.

ESTADO FINAL EM 13/11/2026: infraestrutura do Kwai em nuvem ainda não entregue; rota Oracle desativada; CutMotions e Kuaishou excluídos; demais servidores não homologados; operador físico preservado até migração comprovada.