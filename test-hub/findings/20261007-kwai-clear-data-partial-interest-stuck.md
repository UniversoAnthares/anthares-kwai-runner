# Kwai clear-data probe — PARTIAL (interest stuck)
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-07
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37638909906
JOB: 112852337154
COMMIT: 13c0d7101d6e59b1458fd0d885439f527e11f6a6
SUPERSEDES: none

## Objetivo
Forçar superfície de login via `pm clear com.kwai.video` após sessão cached.

## Resultado
FUNCIONOU:
- `pm clear` retornou Success
- TEST_VALIDITY=OK (23 snapshots com árvore UI)
- Após clear, app saiu do MAIN autenticado e entrou em onboarding fresco: "choose like or dislike to let us know you better. 1/12" com kwai_ctx=True
- Isso prova causalmente que clear-data remove a sessão cached

FALHOU / incompleto:
- Probe não avançou o INTEREST (estado classificado como OTHER; sem tap like/dislike/skip)
- LOGIN_SURFACE_FORCED=0 — hipótese de login surface ainda não exercitada após clear
- Pre-clear ficou no launcher/permission (harness timing), não no MAIN cached deste run

## Evidência decisiva
Log: `[CLEAR] pm_clear_out=Success` → post-clear-1..15 text="choose like or dislike..." kwai=True login_like=0

## Consequência
Não classificar clear-data como FAILED. Próximo teste DEVE avançar INTEREST (like/dislike ou skip) e depois START/MAIN/login. Não repetir o mesmo probe sem handler de INTEREST.
