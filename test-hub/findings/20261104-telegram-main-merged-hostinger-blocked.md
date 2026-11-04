# Telegram WordPress — correções incorporadas, publicação pendente
STATUS: PARTIAL
AREA: wordpress-telegram
DATE: 2026-11-04
COMMIT: wordpress main afb0e072f4517ba6bb052b8cb21734901971f792
SUPERSEDES: test-hub/findings/20261104-telegram-peerid-merged-botpoll-draft-deploy-blocked.md

## Concluído no GitHub
- PR #227: URL Web A do grupo corrigida para https://web.telegram.org/a/#-1001152484758, correspondendo ao ID completo confirmado pelo Bot API. Clique JS simulado PASS; texto e link do tópico copiados.
- PR #228: autenticação por desafio /start do bot via Bot API getUpdates; trava de concorrência e autenticação WordPress. A flag anthares_telegram_bot_polling_ready permanece DESATIVADA.
- PR #229: URL oficial do bot como alternativa caso a conversa no Telegram Web não abra. Parser JS PASS.

## Bloqueios reais
Sem deploy Hostinger nesta intervenção: havia negativa explícita de segurança da ferramenta em execuções remotas anteriores. Não utilizar outro canal para contornar. PHP lint integral após a última alteração, deploy/backup, teste no browser autenticado, ativação da flag e confirmação real /start continuam pendentes. Nenhum envio ao grupo nem despesas efetuados. Envio de usuário como conta pessoal via MTProto é pendência separada.
