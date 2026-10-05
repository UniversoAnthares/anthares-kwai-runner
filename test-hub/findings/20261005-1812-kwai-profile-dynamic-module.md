# Login control discovery alcança Profile e revela bloqueio por módulo dinâmico
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37379937689
JOB: 111999004859
COMMIT: 4d6d927050c6131d0492f280292bbd913aa97778
SUPERSEDES: none

## Objetivo
Descobrir sem credenciais o controle que leva da navegação principal ao formulário de login.

## Resultado
A travessia chegou deterministicamente a MAIN_NAV. A UI expôs com.kwai.video:id/ll_profile como LinearLayout clicável e o texto Profile. Após acioná-lo, o Kwai exibiu modal de módulo dinâmico: "resource downloading" / "you'll have access to all the features when it’s done.", com botão Hide. Nesse estado ainda havia zero candidatos de autenticação e nenhum formulário editável. O exit 21 significa somente que o teste procurou login antes de o recurso Profile ficar disponível.

## Evidência decisiva
STATE=MAIN_NAV; resource-id com.kwai.video:id/ll_profile clickable=true; STATE=PROFILE; tv_loading_title="resource downloading"; tv_loading_content="you'll have access to all the features when it’s done."; btn_cancel="hide"; AUTH_CANDIDATES=0; LOGIN_FORM_FOUND=0.

## Consequência
A rota até Profile está comprovada e NÃO deve ser redescoberta. Próximo teste deve tratar explicitamente o download do módulo dinâmico: aguardar sua conclusão com timeout, observar mudança de estado, fechar/ocultar o modal apenas quando necessário, reabrir Profile e só então procurar controles de login. Não executar novo E2E credenciado antes de comprovar essa transição.
