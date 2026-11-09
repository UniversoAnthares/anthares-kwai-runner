# KW12 — recuperação quando sala se encerra antes de seis horas (09/11/2026)
AREA: kwai-live
OWNER: chatgpt-kw12-recovery
STATUS: PARTIAL_CODE_PROVEN / REAL_STUDIO_AUTH_AND_6H_LIVE_PENDING
LEASE_UNTIL_UTC: 2026-11-09T21:25:00Z

BASELINE_PROVEN: duas salas foram criadas automaticamente no Studio em 09/11; sala 9973552511847 encerrada após ~65 minutos, FFmpeg Hostinger terminou; cron Hostinger `* * * * *` já está configurado com `kw12-cron-tick.sh`; issue de controle do cloud cycle permanece idle; o código `kwai_live_6h_cycle.py` retorna sem consultar Studio quando o estado local indica `active` e ainda faltam minutos para `renew_after`.
FAILED_AVOIDED: não criar outra sala enquanto uma sala remota permanece ativa; não depender de um estado local que pode continuar `active` após encerramento antecipado. Preservar o produtor RTMP Hostinger e a sessão existente.
SUCCESS_SIGNAL: teste isolado mostra retorno conservador quando sala remota está ativa, recuperação da sala apenas após confirmação remota de encerramento, falha segura quando status remoto é desconhecido e propagação de término antecipado ao estado GitHub.
FAILURE_SIGNAL: renovação duplicada, retorno prematuro para sala confirmadamente encerrada, perda de estado ou avanço quando consulta remota é inconclusiva.
TEST_VALIDITY: usar stub de controle GitHub/Studio para os ramos de recuperação e validação Python de sintaxe; testes sintéticos não comprovam live real nem autenticação de Studio.
NOTA: não ativar o workflow enquanto a credencial web persistente do Studio não for validada; manter a rotina Hostinger independente.

EVIDENCE: codificação em `kwai_live_6h_cycle.py`: validação conservadora de `roomStatus`, consulta remota anterior à decisão de aguardar seis horas, estado `ended` por encerramento antecipado, retomada controlada para criar a próxima sala. Verificação sintática Python e presença dos guardas: `KW12_SYNTAX_AND_GUARDS=PASS` em 2026-11-09.
CLOSURE: não ativa novo cron; o workflow já tem agendamento de 30 minutos, protegido por `KWAI_LIVE_6H_ENABLED`; a sessão autenticada do Studio ainda não foi restaurada no executor GitHub. Assim, a prova de seis horas e renovação fica pendente e nenhuma transmissão adicional foi criada por esta intervenção.
