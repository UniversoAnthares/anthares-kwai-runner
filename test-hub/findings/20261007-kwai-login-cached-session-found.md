# Kwai login surface discovery — cached session found
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-07
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37609057022
JOB: 112604992835
COMMIT: 928c28e
SUPERSEDES: none

## Objetivo
Descobrir a superfície real de login do Kwai sem credenciais.

## Resultado
PROVED: o app abre diretamente no feed com uma conta cached já autenticada. Nenhuma tela de login apareceu em 22 snapshots. O estado MAIN foi alcançado em onboarding-2 e permaneceu como RESOURCE_LOADING por ~3 minutos, indicando uma sessão ativa baixando recursos.

Evidência:
- Texto do autor no feed: "المصمم 👑💫أمـــــــــــــــير💫👑"
- Botões de interação presentes: follow, like, comment, share
- Resource IDs confirmam app em MAIN: ll_profile, fl_avatar_follow, tv_author
- Sem nenhum editable node ou login-like node em nenhum snapshot

## Consequência
O próximo passo causal é:
1. Navegar para Profile (ll_profile)
2. Procurar botão de logout/settings
3. Deslogar da conta cached
4. Só então executar autologin com KWAI_LOGIN/KWAI_PASSWORD

Não repetir autologin cego sem antes garantir que o app está no estado de login desejado.
