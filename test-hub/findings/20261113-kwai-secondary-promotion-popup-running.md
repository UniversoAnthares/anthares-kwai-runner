# Kwai secundária: janela promocional impede botão Perfil
STATUS: RUNNING
AREA: kwai
DATE: 2026-11-13
RUN: none
JOB: none
COMMIT: 7b17cb703e94de54830167a1e2dba5e91f02c906
SUPERSEDES: none
OWNER: ChatGPT / Anthares Kwai secondary, path-scoped to native driver + overlay regression.

## BASELINE_PROVEN
Após implantar Neon 77 e atualizar os dois scripts do daemon Windows, quatro ACKs obsoletos foram reconhecidos por leitura RSA do servidor; os dois daemons reiniciaram às 19:11 e a secundária iniciou um job às 19:12. O worker abortou antes de STARTED e antes de qualquer post (rc 81, possible=False) porque a consulta RID_PROFILE não encontrou id_home_bottom_tab_me. O XML salvo baseline-home-0 no executor continha 123 nodes e o RID_PROFILE, enquanto baseline-home-1 continha apenas seis nodes, IDs com.kwai.video.basis:id/view_content, com.kwai.video:id/close_button, com.kwai.video:id/colored_button_bg. A rotina kwai-up/kwai_up.py já prevê exatamente esse modal; o driver tools/kwai_native_cortes.py cobre overlays diferentes, mas não essa combinação.

## FAILED_AVOIDED
Não alterar/fechar uma sessão sem match dos três IDs exatos; não automatizar login, CPF, permissões nem publicação para teste. Não reiniciar nem tocar o Android físico enquanto o daemon principal possuir um STARTED em produção. Não repetir o corte secundário em paralelo; respeitar backoff e fila canônica.

## SUCCESS_SIGNAL
Teste offline com popup dos três IDs, botão correto habilitado, e navegação normal após fechar. Conjunto de IDs incompleto ou close desabilitado deve falhar fechado sem tap. CI do Kwai aprovado; alteração do driver só promovida quando não houver STARTED/UNCERTAIN ativo.

## FAILURE_SIGNAL
Qualquer popup não reconhecido fechado por acidente, testes com Android/publicação, perda da compatibilidade, ou estado da fila alterado pelo QA.
TEST_VALIDITY: simulação XML sanitizada, sem dados do usuário, Android, mídia ou credenciais.
