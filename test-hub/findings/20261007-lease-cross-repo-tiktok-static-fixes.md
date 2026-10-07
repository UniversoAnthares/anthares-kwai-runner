# Lease — correções estáticas cross-repo de TikTok e CI
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-07
RUN: none
JOB: MDE9nE00YIndrW2UFftCo3
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-07T16:15:00Z

## Objetivo
Aplicar somente correções locais, reversíveis e verificáveis em sintaxe Python, gates de CI e bootstrap que mascara falha no repositório anthares-clipper. Nenhuma publicação, sessão, login, credencial, deploy ou chamada externa será executada.

## BASELINE_PROVEN
A auditoria cross-repo de 2026-10-07 identificou `tiktok_web_publish_local.py` com SyntaxError comprovado por `py_compile`, um teste de arquitetura incoerente com o workflow e `bootstrap-android-executor.sh` ignorando falha de `waydroid container start`.

## FAILED_AVOIDED
Não repetir execução do publicador TikTok, não alterar cadência/meta ou identidade da conta TikTok, não migrar token Android sem estratégia de compatibilidade, não iniciar Android/Waydroid real e não alterar sessão/autenticação.

## SUCCESS_SIGNAL
`py_compile` dos arquivos corrigidos passa; testes estáticos relevantes passam ou refletem explicitamente o contrato já declarado pelo workflow; `bash -n` passa; diff não contém segredos nem alterações fora do escopo.

## FAILURE_SIGNAL
Qualquer SyntaxError permanece, o teste passa somente por ser enfraquecido, o bootstrap ainda mascara erro, ou aparece alteração de publicação/sessão/credencial.

## TEST_VALIDITY
Validação exclusivamente offline e determinística: compilação, testes unitários locais, `bash -n`, `git diff --check` e inspeção de diff. Falta de Android/Playwright/serviços externos não conta como PASS.
