# AOI #7 / AOI-01 — Forgejo Hostinger daemon recovery via authenticated hPanel
STATUS: PROVEN
AREA: architecture/forgejo-daemon-hostinger-live
DATE_UTC: 2026-11-11T11:02:52Z
OWNER: chatgpt-hpanel-forgejo-20261111
LEASE: CLOSED
SUPERSEDES: 20261111-forgejo-hpanel-keepalive-lease.md
SOURCE_BLOB_GITHUB: 966e539447a814da72f8db0c8a682cef1603fe0b
PREVIOUS_STATE: source-fixed but Hostinger missing keepalive cron and script
COST_ADDED: 0
SOCIAL_PUBLICATIONS: 0

## Prova direta no ambiente real
1. Proprietário autenticou o navegador dedicado AntharesTinyFish no Hostinger hPanel. Seletor de conta confirmou domínio anthares.us.
2. Hostinger Cron Jobs, antes: 10 linhas de tabela incluindo cabeçalho; dois crons independentes Forgejo existentes: 17 * * * * mirror-avs-cron.sh e 0,30 * * * * git-mirror-hostinger-scheduled.sh. Nenhum comando forgejo_keepalive.sh.
3. Hostinger File Browser v2.63.2-h2 aberto na raiz privada ~/.anthares-forgejo/. Foram carregados 129 itens: bin, custom, data, forgejo.sock, forgejo.log e scripts de espelho presentes; forgejo_keepalive.sh ausente.
4. Nova criação controlada: ~/.anthares-forgejo/forgejo_keepalive.sh. Código extraído da main canônica (blob acima), 2299 caracteres. Editor Ace recebeu o conteúdo e clicou Save; reload da rota exata comprovou persistentEqual=true, actualLength=expectedLength=2299.
5. Hostinger Cron Jobs: modo Personalizado, minuto */5, hora *, dia *, mês *, dia da semana *; comando /bin/bash /home/u566597497/.anthares-forgejo/forgejo_keepalive.sh. HPanel notificou "Tarefa cron criada com sucesso". Após atualização: 11 linhas com cabeçalho, matchingCount=1 e uma linha exata */5 * * * * para o comando. Os crons de espelho foram preservados.
6. Saída do cron efetivo (Hostinger, modal "Cron saída", lida em 2026-11-11T11:02:52Z): FORGEJO_KEEPALIVE_RECOVERED=PASS pid=2880553. O script só emite este marcador depois que curl --unix-socket ~/.anthares-forgejo/forgejo.sock http://unix/api/v1/version retorna 2xx; comprovou start real e resposta local da API.
7. Nenhum comando SSH nem revalidação HTTPS da tentativa anterior bloqueada foram efetuados. Sem alteração de repositórios bare, secrets, tokens, assinaturas, cloud resources ou publicadores.

## Critérios de escopo
PROVEN: script idêntico salvo, cron único instalado, pelo menos uma execução real que iniciou o daemon e recebeu resposta da API por Unix socket.
PENDING: continuidade após múltiplos ciclos, endpoint HTTPS externo e paridade Git completa (incluindo AVS); verificação SSH/HTTPS anterior foi negada pela camada de segurança, bloqueio preservado. Portanto o item mais amplo AOI #7 e a publicação AOI-01 não estão inteiramente concluídos por este recibo.
NO_PUBLIC_HTTP_200_CLAIM: true
SAFE_RECOVERY: no process kill, no prune/force and flock nonblocking.
