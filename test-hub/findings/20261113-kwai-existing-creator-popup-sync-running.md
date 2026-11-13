# Preservar o guard local de popup de nível do criador
STATUS: RUNNING
AREA: kwai
DATE: 2026-11-13
RUN: none
JOB: none
COMMIT: 7cad867ca89391415af022cf6e4a7b0b04339907
SUPERSEDES: none
OWNER: ChatGPT / Kwai native existing local edit

## BASELINE_PROVEN
Após o patch de promoção exata, a leitura do arquivo Windows tools/kwai_native_cortes.py revelou regra local anterior ausente do GitHub: fecha somente create_cancel_button Fechar se o create_user_text identificar Universo Anthares. O arquivo local preservou essa regra ao receber o patch para view_content/close_button. Divergência de 6 linhas impede substituição canônica futura sem perder a proteção existente.
## FAILED_AVOIDED
Não sobrescrever o guard local, nem publicar mídias, reiniciar processos, tocar Android, remover locks ou alterar filas. GitHub código principal tem os testes de popup promocional da PR #2597.
## SUCCESS_SIGNAL
Adicionar a regra local já existente ao GitHub e testar offline owner correto, controles habilitados e inputs inválidos. CI Kwai completo aprovado. Provar hash local contém ambas as regras, sem restart.
## FAILURE_SIGNAL
Remover regra da promoção anterior, fechar popup desconhecido ou alterar publicação real. 
TEST_VALIDITY: XML in memory; nenhuma autenticação, arquivo de mídia ou chamada de dispositivo.
