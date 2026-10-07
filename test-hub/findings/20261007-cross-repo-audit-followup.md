# Cross-repo audit follow-up — fechamento parcial
STATUS: PARTIAL
AREA: github
DATE: 2026-10-07
RUN: none
JOB: 24daa7c683aa
COMMIT: none
SUPERSEDES: 20261007-cross-repo-audit-unresolved.md

## Objetivo

Atualizar o estado do finding inicial da auditoria abrangente dos oito repositórios, sem editar o registro histórico. Este follow-up verifica as duas entregas que haviam ficado incompletas no encerramento automático: o pacote do Telegram relay e a publicação das correções do WordPress.

## Resultado

Nove itens administrativos/técnicos do finding inicial foram encerrados:

1. O relatório detalhado do Telegram relay foi criado em `/home/ubuntu/github-audit/2026-10-07/03-anthares-telegram-relay-report.md`.
2. A correção de acessibilidade do relay foi promovida ao `relay-source.zip`, publicada no commit `acb9e7a5c0490435c5d95043add020f7ea8e4f43` da branch `manus/audit-2026-10-07-03-anthares-telegram-relay` e registrada no [PR #1](https://github.com/UniversoAnthares/anthares-telegram-relay/pull/1).
3. O relatório detalhado do WordPress foi criado em `/home/ubuntu/github-audit/2026-10-07/05-anthares-wordpress-report.md`.
4. As seis alterações estáticas do WordPress foram confirmadas no [PR #15](https://github.com/UniversoAnthares/anthares-wordpress/pull/15), branch `audit/2026-10-07-fixes`.
5. O Plugin URI placeholder do Lovecraft foi corrigido no commit `a5bfc8642957bdc78cdfe55941c7c0c14ab795a2` e enviado ao mesmo PR.
6. O finding inicial foi efetivamente atualizado por este novo registro, como exige a política append-only.
7. Os itens anteriores que apenas diziam que o hub ainda não tinha sido atualizado deixam de ser bloqueios: clipper, transcrição, wiki, home e slideshow agora estão cobertos pelo finding inicial e por este follow-up.
8. O branch local do WordPress foi sincronizado e ficou limpo após a publicação.
9. O branch do relay recebeu testes reproduzidos: 3/3 testes unitários, compileall, `unzip -t` e `git diff --check` passaram.

## Evidência decisiva

- Relay: `PYTHONPATH=.audit-work .audit-work/.venv/bin/python -m unittest discover -s .audit-work/tests -v` retornou 3/3; `unzip -t relay-source.zip` passou; o ZIP contém HTML com `lang="pt-BR"` e viewport.
- WordPress: no branch do PR, `node --check` passou em 37/37 JavaScript, `bash -n` em 3/3 shells, JSON em 2/2 arquivos, `ffprobe` em 18/18 mídias e `git diff --check` passou; o placeholder e as referências estáticas `mapa.webm`/`mapa.mp4` foram eliminados.
- Não houve merge, force-push, deploy, uso de segredos ou chamada real a Telegram, WordPress, Docker, PHP, TikTok, Kwai, YouTube, Cloudflare ou FTPS.

## Pendências ainda abertas

O estado correto não é “aprovado”: restam **40 itens** do finding inicial, agrupados assim: Kwai runner (7), clipper (5), Telegram relay (4), transcrição (6), WordPress (4), wiki (3), home (5) e github-slideshow (6).

Os bloqueios principais continuam sendo toolchains ausentes (Android/Gradle/SDK, PHP/PHPUnit, Docker, Ruby/Jekyll/HTML Proofer e validadores YAML), testes reais com credenciais/serviços externos não executados, decisões de governança/licença/segurança, ausência ou ambiguidade de branding, acessibilidade pendente no WordPress, URL `/regras/` 404 sem substituto confirmado, repositórios placeholder/vazio, PRs sobrepostos e ausência de validação semântica integral dos findings históricos.

## Consequência

O finding inicial permanece como evidência histórica do estado de 49 pendências. Este follow-up é a referência mais nova para o estado após as correções adicionais: 9 itens foram encerrados e 40 permanecem abertos. Antes de qualquer novo teste ou mutação, consultar este arquivo e o `test-hub/README.md`; criar novo finding para cada resultado posterior e não editar os dois registros históricos.
