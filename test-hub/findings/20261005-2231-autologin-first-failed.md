# Kwai autologin real acceptance: first attempt failed
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378867229
JOB: REAL AUTOLOGIN + AUTH PROBE
COMMIT: 1d35dce9f93fa6cf255a443a067f95bfee870056
SUPERSEDES: none

## Objetivo
Executar autologin credenciado E2E (vault + onboarding adaptivo + Profile semântico + credenciais KWAI_LOGIN/KWAI_PASSWORD) e validar estado autenticado via kwai_auth_probe.py.

## Resultado
Job falhou no step "Real disposable Android acceptance" (script kwai_acceptance.sh → kwai_android_autologin.py). O script aceita RC 0 ou 6 (captcha/verificação) como sucesso; qualquer outro RC falha. Credenciais existem (step "Verify credentials exist" passed). Vault instalado. KVM habilitado. Falha ocorreu durante execução do emulator runner (8min20s).

## Evidência decisiva
Run 37378867229 concluído failure. Step "Real disposable Android acceptance" conclusion=failure. Sem artefatos do autologin (step evidence não rodou). Logs não acessíveis via API (403). Possíveis causas: (a) gate "resource downloading" ainda ativo no momento do login; (b) seletor de login/senha mudou; (c) captcha/verificação (RC=6 não tratado como sucesso no acceptance?); (d) falha de rede/ADB intermitente.

## Consequência
Não credenciar autologin como PROVEN. Próximo teste deve incorporar estabilização comprovada (wait30 + profile-after-wait ou restart-after-nav do probe 37378856592) ANTES da fase de login credenciado. Adicionar logging de RC e UI no acceptance para diagnosticar falha exata. Não repetir autologin sem estabilização prévia.