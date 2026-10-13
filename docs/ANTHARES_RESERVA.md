# Anthares-Reserva

Nome oficial do antigo "Render Redundancy". O sistema coordena provedores de Git e de execução independentes; **não** é um runner Docker por si só.

## Provedores e responsabilidades
- Controlador: `anthares-control` (Cloudflare Workers/Durable Objects), autoridade única de fila, lease, fencing e deduplicação.
- Código: GitHub primário; GitLab secundário; Codeberg terciário **somente após espelhamento autenticado e verificação de refs**.
- Execução de testes: GitHub Actions (fallback de CircleCI), GitLab CI quando cota disponível; Codeberg Woodpecker CI e Forgejo Actions somente quando ativados e com runner apropriado.
- Render: executor de aplicações, não substituto de CI Docker hospedado.

## Regras absolutas
1. Nunca executar o mesmo trabalho em dois provedores simultaneamente: single-writer lease no controlador, generation/fencing.
2. Falha de GitHub/GitLab não autoriza automaticamente promover um espelho desatualizado. Comparar HEAD, branches e tags; divergência bloqueia.
3. Não fazer force-push, merge ou sobrescrita automáticos. Sem cascade GitHub→GitLab→Codeberg.
4. Não ativar os dois CI do Codeberg para a mesma bateria. Um único CI é eleito; outro permanece em standby.
5. Não usar o PC do usuário como runner, nem iniciar PowerShell/cmd.
6. CI sem publicação real nas redes sociais; apenas testes isolados.
7. Não declarar Codeberg pronto sem URL real do repositório, credencial válida, SHA/refs comprovados e runner funcional.

## Implantação pendente de autorização/infra
- Provisionar espelho Codeberg e configurar `ANTHARES_CODEBERG_PUSH_URL` e `ANTHARES_CODEBERG_READ_URL` em secrets, sem gravar tokens no Git.
- Validar sincronização fast-forward e SHAs. Manter fluxo `.github/workflows/git-provider-redundancy.yml` manual até prova de credenciais e consistência.
- Solicitar acesso ao Woodpecker hospedado em ci.codeberg.org; a aprovação é humana pelo Codeberg.
- Habilitar Forgejo Actions no repositório Codeberg e verificar disponibilidade de runner hospedado.
- O QA canônico `ci/shared/anthares-browser-runtime-qa.sh` requer Docker daemon. Não rodá-lo em runner Codeberg sem Docker nem declarar equivalência a smoke tests.
- Provar job e logs antes de marcar provedor READY.

## Artefatos preparados
- `.forgejo/workflows/anthares-reserva-smoke.yml`: smoke leve manual, sem sobreposição com QA Docker.
- `.woodpecker.yml`: smoke leve manual; exige Woodpecker habilitado no Codeberg.
- QA Docker de 40 casos já preparado na branch `qa/anthares-browser-github-fallback`, sem sucesso de runner comprovado.
