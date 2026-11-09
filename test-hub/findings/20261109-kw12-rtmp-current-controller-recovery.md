# KW12 — recuperar encerramento antecipado no controlador RTMP vigente

AREA: kwai-live
STATUS: CODE_PROVEN / LIVE_ACCEPTANCE_PENDING
BASELINE_PROVEN: a conta @lucasrosalem já criou duas salas Studio em 2026-11-09; uma terminou depois de ~65 minutos. O cron Hostinger chama kw12-cron-tick.sh a cada minuto. Novo controlador kwai_live_rtmp_cycle.py criava a sala e passava seu RTMP à Hostinger, porém ainda retornava imediatamente quando a issue indicava active antes de renew_after, sem consultar o estado remoto.
FAILED_AVOIDED: retomada duplicada de sala ainda ativa; espera de seis horas por sala já encerrada; criação baseada em status remoto 0/indeterminado ou transitório.
SUCCESS_SIGNAL: consulta remote room antes de decidir aguardar, retorno apenas para roomStatus=1 confirmado, recuperação de encerramento antecipado nos estados terminais estáveis; ciclo continua com exclusão mútua e host cron existentes.
FAILURE_SIGNAL: espera por sala expirada, dupla live na mesma conta, início de nova sala com estado desconhecido.
TEST_VALIDITY: Python AST validado, guardas de estado presentes; o teste não confirma Studio autenticado nem uma LIVE real de seis horas.
EVIDENCE: KW12_RTMP_RECOVERY_SYNTAX_AND_REMOTE_STATE_GUARDS=PASS em 2026-11-09; preservada a chave existente e nenhuma sala criada neste teste.
