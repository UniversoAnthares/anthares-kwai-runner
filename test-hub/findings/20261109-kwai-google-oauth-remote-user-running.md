# KW-09 — correção do acesso remoto e autenticação Google
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-11-09
RUN: pending workflow_dispatch
SUPERSEDES: 20261109-kwai-hosted-credential-auth-running.md

BASELINE_PROVEN: Android hospedado inicia, instala Kwai, oferece noVNC protegido. A execução 42620327925 expirou sem obter a identidade esperada; o cofre da conta lucasrosalem permanece sem sessão autenticada.
FAILED_AVOIDED: Autenticação automática por senha em conta que utiliza login Google; nome incorreto anthares para acesso à interface remota.
SUCCESS_SIGNAL: janela privada acessível com usuário remoto universoanthares; autenticação Google concluída pelo titular; prova positiva do perfil Kwai esperado; cofre criptografado com restaurações independentes.
FAILURE_SIGNAL: login Google indisponível, identidade Kwai incompatível com destino kwai:lucasrosalem, timeout ou exigência de verificação adicional.
TEST_VALIDITY: O fluxo de autenticação não obtém lease Neon e não publica; continua a confirmação estrita da identidade e o firewall de publicação. Usuário Google externo faz autenticação interativa na própria UI. Não registrar senha, cookie ou mídia.
