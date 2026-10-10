# Lease — Kwai bridge recovery orchestrator
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-10
RUN: none
JOB: none
COMMIT: 7c4df97efe024ac24eed2a18dadbdd67c5d1298b
SUPERSEDES: none

## Objetivo
Criar e validar um caminho de recuperação remota da bridge do Codespaces sem usar o PC local, preservando a sessão autenticada do Chrome/Kwai.

## BASELINE_PROVEN
Issue #12 já respondeu anteriormente com chrome_connected=true e kwai_tab_present=true. A bridge depois deixou de responder aos comandos novos. O Chrome/session profile não deve ser reiniciado ou exportado.

## FAILED_AVOIDED
- Não repetir dependência exclusiva do noVNC/porta 6080.
- Não depender de ação manual no PC.
- Não destruir/recriar o perfil autenticado do Chrome.
- Não considerar job verde como prova sem resposta da bridge.
- GitLab espelho atual está sem ref executável; não tratá-lo como executor até bootstrap válido.

## SUCCESS_SIGNAL
Um workflow remoto consegue: (1) verificar a issue #12, (2) detectar bridge sem resposta, (3) tentar recuperar/iniciar o Codespace por API quando houver credencial compatível, (4) postar novo nonce, e (5) observar KWAI_BRIDGE_RESULT correspondente. Após recuperação, profile_check/owner_probe devem comprovar chrome_connected=true, authenticated_ui_detected=true e identity_verified=true para a conta Kwai correta @lucasrosalem.

## FAILURE_SIGNAL
API de Codespaces sem autorização utilizável e ausência persistente de resposta da bridge após tentativa de recuperação.

## TEST_VALIDITY
O harness deve registrar separadamente: autorização da API, estado do Codespace, envio do comando e resultado recebido. Falha de permissão/harness é INVALID/PARTIAL, não falha da sessão Kwai.

## Lease
Área: kwai-login
Expira em no máximo 30 minutos a partir da criação deste finding. Nenhuma publicação real é permitida por este lease.
