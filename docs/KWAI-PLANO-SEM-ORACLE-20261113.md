# Kwai — plano operacional de 13/11/2026: zero custo, sem Oracle, sem PC ou Android físico

STATUS: REVISED_AFTER_REGRESSION_2576. Decisão original relevante: `test-hub/findings/20261005-1741-architecture-decisoes-aceitacao.md`.
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

### Etapa 1 — Qualificar **uma oferta de cessão gratuita** (BLOQUEADA até oferta real)
Buscar provedor reconhecido, patrocinador institucional ou comunidade que autorize **expressamente** a atividade e a persistência, com custo R$0 sem expiração nem billing obrigatório, root KVM/VM, kernel binder/binderfs, 2 vCPU, 4 GiB RAM, 20 GiB disponíveis e rede suficiente para os uploads. Não solicitar cadastro em site suspeito nem empregar conta de fórum que não tenha elegibilidade demonstrada. O patrocinador pode oferecer uma máquina própria; o serviço ainda precisa permitir uso comercial legítimo e sessões persistentes. Exigir documentação da oferta/contrato e identificação do operador; comprovada a cessão, passar para a etapa 2. **O monitor de catálogos atual é somente de leitura; não provisiona.**

### Etapa 2 — Pré-teste em VM entregue (CÓDIGO PRONTO)
No novo host aprovado, rodar `tools/redroid_free_vps_preflight.py`. Exigir KVM/VM equivalente com controle de kernel, Docker privilegiado, dispositivos binder reais e capacidade de upload. `CANDIDATE_FOR_ISOLATED_INSTALL_TEST` autoriza apenas o teste isolado, sem senhas Kwai. Se falhar, encerrar esta oferta e preservar a fila, sem gastar.

### Etapa 3 — Instalar Android e homologar apps (CÓDIGO BASE PRONTO)
Usar o cloud-init portável `infra/oci-android/redroid-firstboot.cloud-config.yml` **somente como bootstrap Linux genérico em provedor não Oracle**, mantendo digests fixos para imagens ARM64/AMD64, ADB vinculado a loopback, persistência do armazenamento e health/reboot. Validar `sys.boot_completed=1`, funcionamento Kwai/Kwai Lite, contas corretas e reinicialização sem precisar do PC.

### Etapa 4 — Ligar duas contas à fila Neon e provar postagens (CÓDIGO BASE PRONTO)
Implantar a função `cortesqueue` no projeto Neon efetivamente autorizado, com `kwai-persistent-cloud-identity.mjs` e cliente `tools/kwai_persistent_cloud_queue.py`. A função de produção não estava no escopo do conector Neon disponível em 13/11/2026; obter acesso ao projeto correto é um impedimento próprio. Configurar token exclusivo da VM, impedir tarefas paralelas entre dispositivos, preservar `lease_generation`, reconciliação de publicação incerta, prova independente do post real em cada conta, janelas de 06–23h e idempotência.

### Etapa 5 — Migrar sem perda ou duplicação (AINDA NÃO AUTORIZADA)
Exigir todos os oito comprovantes `android_execution.cloud_cutover.required_proofs`; só então aprovar `cloud_cutover.enabled=true` por alteração revisada. Confirmar ciclo completo com computador e Android físico desligados, persistência após reboot, links públicos nas duas contas e custo zero. Se o executor remoto falhar, deixar tarefas na fila; nunca repostar estado incerto.

## Se nenhuma cessão gratuita cumprir requisitos
O requisito financeiro impede o provisionamento em hospedagem comercial. A solução passa a depender de **nova decisão explícita do titular** para uma das alternativas: autorizar um servidor pago de baixo custo, permitir temporariamente hardware Android remoto do próprio usuário ou negociar cessão/patrocínio gratuito com termos aprovados. Sem essa decisão ou uma VPS cedida, o plano encerra a fase de pesquisa como BLOQUEADO_POR_RECURSO_REAL. Não reabrir Oracle, CutMotions ou GitHub Android para simular progresso.

## Referências diretas
- Evidência de exclusões: `test-hub/findings/20261005-1741-architecture-decisoes-aceitacao.md`.
- Custos oficial Cloudflare: https://developers.cloudflare.com/containers/platform/pricing/
- Sessões do SpawnDroid: https://spawndroid.io/pricing/ e https://spawndroid.io/changelog/
- Host Android pago: https://hubsim.com/
- Critérios da comunidade: https://freevps.org/ e https://fossvps.org/
- Pré-teste: `tools/redroid_free_vps_preflight.py`, `tests/test_redroid_free_vps_preflight.py`.
- Roteamento protegido: `ci-hub/executor-routing.json`, `docs/KWAI-CLOUD-CUTOVER-CONTRACT.md`.

ESTADO FINAL EM 13/11/2026: infraestrutura do Kwai em nuvem ainda não entregue; rota Oracle desativada; CutMotions e Kuaishou excluídos; demais servidores não homologados; operador físico preservado até migração comprovada.