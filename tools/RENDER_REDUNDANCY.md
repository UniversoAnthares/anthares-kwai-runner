# Redundância do Render no ecossistema Anthares

## Arquitetura

O Render funciona como provedor de execução. A autoridade persistente permanece em `anthares-control`, no Cloudflare Workers/Durable Objects. Essa camada conserva fila, deduplicação, lease, heartbeat, `lease_generation`, fencing e decisão de failover.

Os provedores de execução disponíveis são:

- Render: serviços web e workers já implantados.
- GitHub Actions: execução hospedada e independente do Render.
- GitLab SaaS runners: segundo provedor hospedado e independente do Render/GitHub.
- Cloudflare Workers: endpoints de controle, filas, Durable Objects e tarefas compatíveis com o runtime Workers.

## Invariantes

1. Uma operação possui no máximo um lease ativo.
2. Toda troca de provedor incrementa `lease_generation`.
3. Um provedor recebe failover quando está `READY`.
4. O conteúdo executado no provedor de destino corresponde ao checkpoint do lease por commit ou `content_id` equivalente.
5. Divergência de conteúdo bloqueia a execução.
6. Um lease transferido permanece no provedor atual até renovação, conclusão, expiração ou novo failover explícito.
7. Cloudflare permanece como autoridade de estado durante queda completa do Render.
8. O PC fica fora do runtime de redundância.

## O que este sistema cobre

- queda de um serviço Render com preservação do plano de controle;
- transferência de execução para GitHub/GitLab quando o trabalho é compatível com runner efêmero;
- retries, heartbeat e fencing já existentes no `anthares-control`;
- deduplicação de publicação;
- validação automática da saúde do Cloudflare e dos testes de failover;
- continuidade do sistema com o Render indisponível.

## Limite técnico atual

GitHub Actions e GitLab CI são executores efêmeros. Eles cobrem jobs, builders, validações, publicação e automações finitas. Um serviço HTTP público e continuamente residente que dependa de navegador completo/Playwright exige um runtime persistente. O plano de controle, as filas e os trabalhos compatíveis permanecem operacionais durante essa indisponibilidade.

## Validação

O workflow `.github/workflows/render-redundancy-acceptance.yml` executa três grupos e também roda periodicamente no `main`:

1. política: testes existentes do `provider_router.py` e cenários Render → GitHub → GitLab;
2. plano de controle: `/health` e `/failover-self-test` públicos no `anthares-control`, exigindo estado persistente, fila ligada e failover Render → GitHub;
3. independência: o Render é sondado como provedor; a aprovação depende do Cloudflare continuar saudável e com fila ligada.

`/git-provider-self-test` é um endpoint protegido e deve ser exercitado somente por clientes autenticados.

O arquivo `tools/render_redundancy_acceptance.py` verifica:

- failover quando Render cai;
- segundo failover GitHub → GitLab;
- incremento de geração;
- permanência do lease no provedor atual após recuperação do Render;
- bloqueio de checkpoint divergente;
- recuperação após expiração do lease.
