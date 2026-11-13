# Seletor Próximo da secundária: teste isolado aprovado
STATUS: PROVEN
AREA: kwai
DATE: 2026-11-13
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43530067207
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43530067207/job/132245259370
COMMIT: f754999efa12897a65d8b7238baa36032716e470
SUPERSEDES: 20261113-kwai-secondary-next-control-running.md

## Resultado
No XML real da conta secundária, edit_next_button (clickable, enabled, bounds [555,2052][1029,2134]) contém next_button_normal ("Próximo") e é irmão do botão de publicação direta edit_post_button. O seletor original reconhecia o filho Próximo não clicável; o driver agora aceita somente o pai clicável, habilitado, visível e vinculado ao filho semântico Próximo, especificamente em universoanthares, com recusa segura para controles desabilitados. O caminho Kwai Lite permanece sem alteração.
CI 43530067207: Node 37 pass, 0 fail; KWAI_SECONDARY_EDITOR_CLICKABLE_NEXT_PARENT_PASS, KWAI_SECONDARY_EDITOR_DISABLED_NEXT_FAIL_CLOSED_PASS, ALL_CANONICAL_WINDOWS_KWAI_REGRESSIONS_PASS. Nenhum dispositivo real ou postagem de teste no CI.
## Limites
A interação real ainda exige prova: a ação física do pai e do filho pode coincidir geometricamente. Se a tela continuar presa, capturar nova evidência e investigar inicialização do editor sem clicar Publicar prematuramente. Não promover rollout concorrente enquanto lease secundário estiver ativo. O arquivo Windows não foi alterado nesta homologação de CI.
