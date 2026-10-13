# Anthares-Reserva

Nome oficial do antigo "Render Redundancy". O sistema coordena provedores de Git e de execução independentes; **não** é um runner Docker por si só.

## Provedores e responsabilidades
- Controlador geral: `anthares-control` (Cloudflare Workers/Durable Objects), autoridade única de fila, lease, fencing e deduplicação.
- Anthares Remote / ARA: `anthares-ara-backup.anthares1.workers.dev` fornece um controle ARA independente com estado durável em Cloudflare Durable Objects. Os controles Render (`anthares-ara-control` e `anthares-ara-infra-canary-v2`) permanecem como alternativas enquanto estiverem disponíveis.
- Código: GitHub primário; GitLab secundário; Codeberg terciário **somente após espelhamento autenticado e verificação de refs**.
- Execução de testes: GitHub Actions (fallback de CircleCI), GitLab CI quando cota disponível; Codeberg Woodpecker CI e Forgejo Actions somente quando ativados e com runner apropriado.
- Render: executor de aplicações e fallback de serviços; não deve ser autoridade única de persistência do Anthares Remote.

## Estado comprovado do Anthares Remote — 2026-10-13
- O controle Cloudflare ARA está implantado e responde à autenticação assinada do MCP.
- O supervisor Windows possui três candidatos de controle: Render principal, Render canary e Cloudflare ARA.
- O `force-tertiary.flag` foi ativado no runtime canônico, promovendo o controle Cloudflare sem apagar os fallbacks Render.
- O MCP selecionou `https://anthares-ara-backup.anthares1.workers.dev` como `control_origin` com o dispositivo conectado.
- Execução real concluída pelo caminho Cloudflare: `echo CLOUDFLARE-ARA-OK`, status `done`, exit code 0.
- A fila estava sem trabalhos pendentes ou incertos antes da mudança; portanto a promoção não cortou um lease ativo.
- O PostgreSQL gratuito do Render deixa de ser dependência obrigatória do caminho ativo. Sua futura expiração não deve interromper o controle primário Cloudflare.

## Regras absolutas
1. Custo operacional obrigatório: R$ 0. Não ativar plano pago, cobrança, cartão ou recurso com cobrança potencial.
2. Nunca executar o mesmo trabalho em dois provedores simultaneamente: single-writer lease no controlador, generation/fencing.
3. Falha de GitHub/GitLab não autoriza automaticamente promover um espelho desatualizado. Comparar HEAD, branches e tags; divergência bloqueia.
4. Não fazer force-push, merge ou sobrescrita automáticos. Sem cascade GitHub→GitLab→Codeberg.
5. Não ativar os dois CI do Codeberg para a mesma bateria. Um único CI é eleito; outro permanece em standby.
6. Não usar o PC do usuário como runner. O Anthares Remote pode administrar o próprio runtime, mas não transforma o PC em infraestrutura de CI/publicação de nuvem.
7. CI sem publicação real nas redes sociais; apenas testes isolados.
8. Não declarar Codeberg pronto sem URL real do repositório, credencial válida, SHA/refs comprovados e runner funcional.
9. Não voltar a tornar o PostgreSQL Render autoridade única de estado do ARA.

## Implantação pendente de autorização/infra
- Provisionar espelho Codeberg e configurar `ANTHARES_CODEBERG_PUSH_URL` e `ANTHARES_CODEBERG_READ_URL` em secrets, sem gravar tokens no Git.
- Validar sincronização fast-forward e SHAs. Manter fluxo `.github/workflows/git-provider-redundancy.yml` manual até prova de credenciais e consistência.
- Solicitar acesso ao Woodpecker hospedado em ci.codeberg.org; a aprovação é humana pelo Codeberg.
- Habilitar Forgejo Actions no repositório Codeberg e verificar disponibilidade de runner hospedado.
- O QA canônico `ci/shared/anthares-browser-runtime-qa.sh` requer Docker daemon. Não rodá-lo em runner Codeberg sem Docker nem declarar equivalência a smoke tests.
- Provar job e logs antes de marcar provedor READY.

## Artefatos preparados
- `cloudflare-ara-backup/`: controle ARA gratuito com Durable Object e protocolo compatível com agente/MCP.
- `.forgejo/workflows/anthares-reserva-smoke.yml`: smoke leve manual, sem sobreposição com QA Docker.
- `.woodpecker.yml`: smoke leve manual; exige Woodpecker habilitado no Codeberg.
- QA Docker de 40 casos já preparado na branch `qa/anthares-browser-github-fallback`, sem sucesso de runner comprovado.
