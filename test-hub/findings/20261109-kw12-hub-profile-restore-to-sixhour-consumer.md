# KW-12 — usar o perfil criptografado existente no ciclo de seis horas
AREA: kwai-live
OWNER: ChatGPT KW12
STATUS: RUNNING
BASELINE_PROVEN: workflow_dispatch 42695769045 restaurou com sucesso o artefato criptografado do Anthares Browser Hub (KW12_EXISTING_PROFILE_RESTORED=1), mas a autenticação remota do Studio foi recusada (KW12_REMOTE_STUDIO_SESSION=NOT_AUTHORIZED). O job six_hour_cycle atual ignora esse perfil e tenta usar segredo KWAI_LIVE_STORAGE_STATE_B64 ausente. A flag de agendamento KWAI_LIVE_6H_ENABLED está ausente.
FAILED_AVOIDED: não ativar live com perfil desautenticado; não criar salas repetidas; preservar cron de Hostinger e execuções de outros agentes.
SUCCESS_SIGNAL: workflow de 6h restaura o perfil cifrado existente com chave já instalada, passa seu diretório ao controlador com Chromium persistente, limpa arquivos temporários em qualquer saída; probe retorna falha quando sessão remota não está autorizada.
FAILURE_SIGNAL: live acionada apesar de perfil ausente/desautenticado; armazenamento temporário mantido; segredo exposto em logs; caminhos de recuperação afetados.
TEST_VALIDITY: testes de sintaxe e inspeção de paths, com status da sessão do Studio e live real avaliados separadamente.
LEASE_UNTIL: 2026-11-09T21:30:00Z
