# TikTok restore alcança revisão correta mas não restaura estado
STATUS: FAILED
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37389058316
JOB: 112029516121
COMMIT: 3e1b05f25560567e154c8b95447a1e5bac0858e6
SUPERSEDES: test-hub/findings/20261005-1935-tiktok-restore-identity-running.md

## Objetivo
Provar restore central e identidade com revisão Render exata.

## Resultado
A revisão correta foi alcançada: health mudou de 55b0d581 para f9ed83d7 e o guard passou. O request autenticado ao Render executou restore com OIDC Cloudflare delegado, mas retornou bootstrapped=false e central_restored=false. Identidade não foi executada por fail-closed.

## Evidência decisiva
SESSION_RESTORE_SAFE={"bootstrapped": false, "central_restored": false, "identity_verified": false, "ok": true, "ready_for_tiktok": false}.

## Consequência
Não repetir restore opaco. Instrumentar apenas metadados seguros do GET central para separar HTTP 401/403, 404/ausente, payload inválido e erro de transporte. Não publicar e não testar identidade enquanto bootstrapped=false.
