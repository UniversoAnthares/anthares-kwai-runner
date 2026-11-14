# Agente 05 — recuperação segura de sessão SpawnDroid
STATUS: RUNNING
AREA: session
DATE: 2026-11-14
RUN: none
JOB: none
COMMIT: 5db0bf2ef1e0ed0f1cb930a563090415d686cd0e
SUPERSEDES: none
OWNER: AGENTE 05 — somente arquivos novos tools/kwai_spawndroid_session_recovery.py e tests/test_kwai_spawndroid_session_recovery.py

## BASELINE_PROVEN
Runner Android é destruído no término (SpawnDroid Core concepts). Hobby = 200 minutos/mês, 1 slot, 15 minutos/sessão. O integrador kwai_spawndroid_stable_hub.py efetua somente canário sem login. Agentes 02/03/04 controlam seus adaptadores e publicações.

## FAILED_AVOIDED
Sem cópia de /data/data, cookies, storage_state, backups ADB, tokens entre aplicativos, MFA/CAPTCHA contornado, novo vault, sessão remota faturável, publicação ou mudança Neon. Kuaishou Open Platform não comprova autorização para Kwai brasileiro. Sem alterar adaptador do Agente 02.

## SUCCESS_SIGNAL
Testes offline reproduzem duas contas isoladas, verificação de identidade em sessão nova, fechamento atestado, barreira para MFA, identidade errada, expiração, publicação incerta, quota e falha de término. Estados sem credenciais. Aceite real condicionado às provas Agentes 02/03/04.

## FAILURE_SIGNAL
Qualquer READY com conta errada, upload incerto, sessão anterior sem término, sessão reutilizada, desafio humano, evidência expirada ou publicação sem autorização.

TEST_VALIDITY: apenas offline e provedores simulados; zero minutos consumidos, zero mídia e zero login.
