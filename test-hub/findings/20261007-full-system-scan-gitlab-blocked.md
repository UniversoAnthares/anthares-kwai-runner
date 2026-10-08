# Full system scan — GitLab integration and reproducible defects
STATUS: PARTIAL
AREA: github
DATE: 2026-10-07
RUN: none
JOB: 7fa7adcfabac
COMMIT: none
SUPERSEDES: 20261007-cross-repo-audit-followup.md

## Objetivo

Registrar o resultado da nova varredura total dos oito repositórios, incluindo código, documentação, workflows, testes, assets, logs, histórico Git, PRs e findings disponíveis, e registrar explicitamente o estado da integração GitLab↔GitHub.

## Resultado

A auditoria paralela terminou sem falha de execução e produziu oito relatórios detalhados. Foram confirmados defeitos reais que ainda impedem a aceitação plena: workflow TikTok sem executor e sem ledger; regex de remote_id incorreta; exposição de storage_state/cookies; falsa idempotência após falha no relay; JSON assinado não-objeto causando 500; chunks WordPress calculados com floor; atualização de lease não atômica; execução de script Forgejo remoto sem pin/hash; configurações Reveal ignoradas; staging com push force após falha; heartbeat Kwai incompatível com capabilities exigidas; contrato v16 no código contra endpoint público v12; limite da transcrição aplicado apenas após download; e cookies históricos do YouTube que precisam ser rotacionados.

O GitLab não pôde ser confirmado: o navegador permanece em `gitlab.com/users/sign_in`, não há `glab`, token, remote GitLab ou conector verificável. Os workflows de mirror falharam porque `GITLAB_MIRROR_URL` estava vazio. Não há evidência válida de que GitLab↔GitHub esteja operacional.

## Evidência decisiva

- O workflow TikTok termina após o gate sem chamada a planner/executor/complete/ledger.
- Reprodução do relay: falha de transporte 503 seguida de mesmo `request_id` retorna 200 `duplicate=true`; JSON assinado `[]` retorna 500.
- Reprodução estática do Kwai: heartbeat `cuts,tiktok,control` não satisfaz papéis `kwai` e `kwai_live`; endpoint público confirmou v12 enquanto código/scripts exigem v16.
- WordPress: `floor` de chunks, SELECT→UPDATE de lease e script Forgejo remoto sem verificação são achados estáticos nos arquivos citados.
- Slideshow: opções de Reveal não chegam ao initialize; `script/stage` não aborta após build e contém `git push --force`.
- Transcrição: hard cap ocorre após `yt-dlp`; histórico público contém cookies de sessão/auth do YouTube, removidos do working tree mas ainda alcançáveis no histórico.

## Consequência

Não classificar o projeto como plenamente implementado. Corrigir primeiro segurança e integridade de publicação; depois alinhar contratos, idempotência e leases; em seguida configurar GitLab autenticado e comparar SHA de branches/tags. Não executar mirror, force-push, publicação real ou rotação de credenciais sem autorização e ambiente adequados.

Os relatórios locais completos estão em `/home/ubuntu/github-audit/2026-10-07/full-system-scan-2026-10-07.md` e nos oito arquivos `*-full-scan.md` do diretório da auditoria. Nenhum código, PR, branch, remote ou deploy foi alterado por esta varredura.
