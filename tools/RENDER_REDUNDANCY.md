# Redundância do Render no ecossistema Anthares

## Arquitetura

O Render passa a ser tratado como um provedor de execução, e não como autoridade do sistema.

A autoridade persistente permanece em `anthares-control`, no Cloudflare Workers/Durable Objects. Essa camada conserva fila, deduplicação, lease, heartbeat, `lease_generation`, fencing e decisão de failover.

Os provedores de execução disponíveis são:

- Render: serviços web e workers já implantados.
- GitHub Actions: execução hospedada e independente do Render.
- GitLab SaaS runners: segundo provedor hospedado e independente do Render/GitHub.
- Cloudflare Workers: endpoints de controle, filas, Durable Objects e tarefas compatíveis com o runtime Workers.

## Invariantes

1. Uma operação possui no máximo um lease ativo.
2. Toda troca de provedor incrementa `lease_generation`.
3. Um provedor só recebe failover quando está `READY`.
4. O conteúdo executado no provedor de destino deve corresponder ao checkpoint do lease por commit ou `content_id` equivalente.
5. Divergência de conteúdo bloqueia a execução.
6. A recuperação do Render não toma de volta um lease já transferido.
7. Cloudflare permanece como autoridade de estado mesmo durante queda completa do Render.
8. O PC não participa do runtime de redundância.

## O que este sistema cobre

- queda de um serviço Render sem perda do plano de controle;
- transferência de execução para GitHub/GitLab quando o trabalho é compatível com runner efêmero;
- retries, heartbeat e fencing já existentes no `anthares-control`;
- deduplicação de publicação;
- validação automática da saúde do Cloudflare e dos testes de failover;
- continuidade do sistema com o Render indisponível.

## Limite técnico atual

GitHub Actions e GitLab CI são executores efêmeros. Eles substituem jobs, builders, validações, publicação e automações finitas. Um serviço HTTP público e continuamente residente que dependa de navegador completo/Playwright continua exigindo um runtime persistente. O plano de controle, as filas e os trabalhos compatíveis permanecem operacionais durante essa indisponibilidade.

## Validação

O workflow `.github/workflows/render-redundancy-acceptance.yml` executa três grupos:

1. política: testes existentes do `provider_router.py` e cenários Render → GitHub → GitLab;
2. plano de controle: `/health`, `/failover-self-test` e `/git-provider-self-test` no `anthares-control`;
3. independência: o Render é sondado apenas como informação; a aprovação depende do Cloudflare continuar saudável e com fila ligada.

O arquivo `tools/render_redundancy_acceptance.py` verifica:

- failover quando Render cai;
- segundo failover GitHub → GitLab;
- incremento de geração;
- ausência de failback automático;
- bloqueio de checkpoint divergente;
- recuperação após expiração do lease.
